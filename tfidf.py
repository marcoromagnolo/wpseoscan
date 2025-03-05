from datetime import datetime
from os.path import split

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import vstack
import numpy as np
import joblib
import io
import os
import requests
import mysql.connector
from settings import DB_SETTINGS
from settings import WORK_DIR, OPENAI_SECRET


class Tfidf:

    def __init__(self, logger):
        self.logger = logger
        self.vectorizer = None
        self.work_dir = WORK_DIR
        # Ensure the storage directory exists
        os.makedirs(self.work_dir, exist_ok=True)
        self.vectorizer = self.load_object("vectorizer")
        self.tfidf_matrix = self.load_object("tfidf_matrix")
        self.post_ids = self.load_object("post_ids")
        self.post_contents = self.load_object("post_contents")
        if not self.vectorizer:
            self.build_vectorizer()


    def get_post_ids(self):
        """Get the document list of id"""
        return self.post_ids


    def get_post_contents(self):
        return self.post_contents
    

    def serialize_object(self, obj):
        """Serialize an object to binary using joblib."""
        buffer = io.BytesIO()
        joblib.dump(obj, buffer)
        buffer.seek(0)
        return buffer.read()


    def deserialize_object(self, binary_data):
        """Deserialize an object from binary using joblib."""
        buffer = io.BytesIO(binary_data)
        return joblib.load(buffer)


    def save_object(self, object_name, obj):
        """Save a serialized object to a file."""
        file_path = os.path.join(self.work_dir, f"{object_name}.pkl")
        with open(file_path, 'wb') as f:
            joblib.dump(obj, f)


    def load_object(self, object_name):
        """Load a serialized object from a file."""
        file_path = os.path.join(self.work_dir, f"{object_name}.pkl")
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                return joblib.load(f)
        return None


    def build_vectorizer(self, data=None):
        """Build the vectorizer object data by data: [( 1, 'first document text' ), (2, 'secondo document text'), ...] """

        self.vectorizer = TfidfVectorizer(strip_accents="unicode", stop_words="english",
                                          token_pattern=r"(?u)\b\d*[A-Za-z]+[\w\-\_]*\b")
        self.tfidf_matrix = None
        self.post_ids = []
        self.post_contents = []
        
        # update data
        if data:
            self.post_ids = [row[0] for row in data if row[0] is not None]
            self.post_contents = [row[1] for row in data if row[1] is not None]
            self.tfidf_matrix = self.vectorizer.fit_transform(self.post_contents)

        # Save
        self.save_object("vectorizer", self.vectorizer)
        self.save_object("tfidf_matrix", self.tfidf_matrix)
        self.save_object("post_ids", self.post_ids)
        self.save_object('post_contents', self.post_contents)
        self.save_on_db()

    def open_connection(self):
        db_connection = mysql.connector.connect(**DB_SETTINGS)
        return db_connection

    def save_vector_state(self):
        db_connection = self.open_connection()
        db_cursor = db_connection.cursor()

        try:
            query = "INSERT INTO vector_state (id, creation_time) VALUES (%s, %s, %s)"
            db_cursor.execute(query, (1, datetime.now(), ))
            db_connection.commit()
        finally:
            db_cursor.close()
            db_connection.close()


    def get_vector_state(self):
        db_connection = self.open_connection()
        db_cursor = db_connection.cursor()

        try:
            query = "SELECT id, creation_time FROM vector_state () VALUES (%s, %s) WHERE id=1"
            db_cursor.execute(query)
            return db_cursor.fetchone()

        finally:
            db_cursor.close()
            db_connection.close()


    def get_post_words(self, post_id):
        db_connection = self.open_connection()
        db_cursor = db_connection.cursor()
        query = "SELECT names from posts WHERE post_id=%s"

        try:
            db_cursor.execute(query, (post_id,))
            row = db_cursor.fetchone()
            if row:
                return row[0].split(" ")
        finally:
            db_cursor.close()
            db_connection.close()

    def get_post_top_keywords(self, post_id):
        db_connection = self.open_connection()
        db_cursor = db_connection.cursor()
        query = "SELECT keyword, post_id from post_top_keywords WHERE post_id=%s"

        try:
            db_cursor.execute(query, (post_id,))
            return db_cursor.fetchall()
        finally:
            db_cursor.close()
            db_connection.close()

    def save_on_db(self, threshold=0.1, top_n=3):
        db_connection = self.open_connection()
        db_cursor = db_connection.cursor()

        # Get feature names (words)
        feature_names = np.array(self.vectorizer.get_feature_names_out())

        try:
            for i, post_id in enumerate(self.post_ids):
                array = self.tfidf_matrix[i].toarray()

                names = feature_names[np.where(array > threshold)[1]]
                query = "INSERT INTO posts (i, post_id, names) VALUES (%s, %s, %s)"
                db_cursor.execute(query, (i, post_id, " ".join(names)))
                db_connection.commit()

                # Get indices of top N words sorted by TF-IDF score

                sorted_indices = np.argsort(array).flatten()[::-1]
                top_keywords = feature_names[sorted_indices][:top_n]

                # insert in db
                for top_keyword in top_keywords.tolist():
                    query = "INSERT INTO post_top_keywords (post_id, keyword) VALUES (%s, %s)"
                    db_cursor.execute(query, (post_id, top_keyword))
                    db_connection.commit()

        finally:
            db_cursor.close()
            db_connection.close()


    def get_post(self, post_id):
        db_connection = self.open_connection()
        db_cursor = db_connection.cursor()
        query = "SELECT post_id, post_keywords, creation_time from posts WHERE post_id=%s"

        try:
            db_cursor.execute(query, (post_id,))
            return db_cursor.fetchall()
        finally:
            db_cursor.close()
            db_connection.close()


    def get_most_similar_document_id(self, document_id, document_text):
        """Update the similarity for a specific page."""

        if not document_id:
            print(f"Empty id document")
            return

        if not document_text:
            print(f"Empty text document")
            return

        new_tfidf_matrix = self.vectorizer.transform([document_text])

        # Compute cosine similarity with all existing post_contents
        similarity = cosine_similarity(new_tfidf_matrix, self.tfidf_matrix)

        # Get the max similarity score and its index
        max_similarity_score = similarity.max().item()
        most_similar_document_id = None
        if max_similarity_score > 0:
            max_similarity_index = similarity.argmax()

            # Find the corresponding page ID using the index
            most_similar_document_id = self.post_ids[max_similarity_index] if self.post_ids else None
            print(f"This document is most similar to id:{most_similar_document_id} with a similarity of {max_similarity_score}")

        # Save the vectorizer
        self.save_object("vectorizer", self.vectorizer)

        # Save the new tfidf_matrix
        self.tfidf_matrix = vstack([self.tfidf_matrix, new_tfidf_matrix])
        self.save_object("tfidf_matrix", self.tfidf_matrix)

        # Save the new post_ids
        self.post_ids.append(document_id)
        self.save_object("post_ids", self.post_ids)

        return most_similar_document_id


    def compare_texts(self, text1, text2):

            # Create headers
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {OPENAI_SECRET}"
                }

            # Create body
            data = {
                "model": 'gpt-3.5-turbo',
                "messages": [
                        {"role": "system", "content": "You are a professional journalist evaluating the similarity of two articles. Two articles are considered similar if they discuss the same topic, cite the same sources or protagonists, and present the same informations."},
                        {'role': 'user', 'content': f"This is the first article: {text1}."},
                        {'role': 'user', 'content': f"This is the second article: {text2}."},
                        {'role': 'user', 'content': f"Reply with 'true' if articles are similar otherwise reply with 'false'."},
                    ],
                "temperature": 0,
                "response_format": {"type": "text"}
            }
            return self.call_openapi(headers, data)


    def call_openapi(self, headers, data):
        self.logger.info(f"Request: {str(data)}")
        url = "https://api.openai.com/v1/chat/completions"
        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 200:
            result = response.json()  # Decodifica la risposta in formato JSON
            out = result["choices"][0]["message"]["content"]
            self.logger.info(f"Response: {out}")
            return out in {"true", "True", "TRUE", "1", "yes", "y"}

        else:
            self.logger.info(f"Errore: {response.status_code}")
            self.logger.info(response.text)

        return False