import spacy
from sentence_transformers import SentenceTransformer, util

# Load spaCy model for entity recognition
nlp = spacy.load("it_core_news_sm")

# Initialize the SentenceTransformer for semantic similarity
model = SentenceTransformer('all-MiniLM-L6-v2')

# Function to extract entities from an article using spaCy
def extract_entities(posts):
    doc = nlp(posts)
    entities = [ent.text for ent in doc.ents]
    return entities


# Function to perform semantic search using SentenceTransformer
def semantic_search(query, articles):
    # Encode the query and the articles
    article_texts = list(articles.values())
    embeddings = model.encode(article_texts, convert_to_tensor=True)
    query_embedding = model.encode(query, convert_to_tensor=True)

    # Compute cosine similarities between the query and each article
    cosine_scores = util.pytorch_cos_sim(query_embedding, embeddings)[0]

    # Get the best match (highest score)
    best_match_idx = cosine_scores.argmax().item()
    best_match_article = list(articles.keys())[best_match_idx]
    best_score = cosine_scores[best_match_idx].item()

    return best_match_article, best_score

