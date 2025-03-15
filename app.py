import json
import re

import werkzeug.exceptions
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import wp
import settings
import pidman
import logg
# from tfidf import Tfidf
import openai
from bs4 import BeautifulSoup, NavigableString

pidman.add_pid_file("wpseoscan.pid")

logger = logg.create_logger('app')

# Set Flask app
app = Flask(__name__)

@app.errorhandler(werkzeug.exceptions.NotFound)
def handle_bad_request(e):
    logger.warning(str(e))
    return 'Not Found', 404


@app.errorhandler(werkzeug.exceptions.BadRequest)
def handle_bad_request(e):
    logger.warning(f"Bad request from ip: {request.remote_addr} {str(e)}")
    return 'Bad Request', 400


@app.errorhandler(Exception)
def handle_generic_error(e):
    logger.error(e, exc_info=True)
    return 'Error', 500


@app.route('/', methods=['GET'])
def health_check():
    """
    Health check endpoint to verify the service is running.
    """
    return jsonify({"status": "running"}), 200


def update_anchors(content):
    soup = BeautifulSoup(content, 'html.parser')

    # get all entities from the content
    result_text = openai.completions(messages=[
        {"role": "system",
         "content": "Sei un SEO Content Specialist e devi individuare tutte le entità contenute in un contenuto HTML. Rispondi solo con un oggetto JSON valido, senza spiegazioni."},
        {'role': 'user',
         'content': f"Estrai tutte le entità (persone, luoghi, organizzazioni, momenti storici, eventi, prodotti, concetti, opere e lingue) dal seguente articolo in modo che possano essere utilizzati com anchor text per creare link ad altri articoli ed aumentare il SEO: {content}"},
        {"role": "user",
         "content": "Rispondi esclusivamente con un oggetto JSON valido nel seguente formato: {\"entities\": [\"entity1\", \"entity2\", ...]}"}])
    if result_text.startswith("```json"):
        result_text = result_text[8:-3]
    if result_text.startswith("```"):
        result_text = result_text[3:-3]
    result = json.loads(result_text)
    if 'entities' not in result:
        return jsonify({"error": "Invalid response from OpenAI API"}), 500

    # replace entities with anchor text
    titles = {}
    p_tags = soup.find_all('p')
    for entity in result['entities']:

        # skip unwanted entities
        if entity.lower() in ['iflscience', 'sciencealert', 'interestingengineering']:
            continue

        # skip numbers
        if entity.isdigit():
            continue

        titles[entity] = wp.search_wp_post_titles(entity)

        if titles[entity]:
            post_id = openai.completions(messages=[
                {"role": "system",
                 "content": "Sei un SEO Content Specialist e devi scegliere il giusto articolo da associare ad un anchor text."},
                {'role': 'user',
                 'content': f'Scegli per questa anchor text: "{entity}" uno fra i seguenti titoli: {titles}'},
                {'role': 'user', 'content': f"Restituisci solo la chiave numerica associata al titolo scelto."}])

            url = wp.get_post_guid(int(post_id))

            for p_tag in p_tags:
                if entity in p_tag.text:
                    # Find the position of the entity in the text
                    text = p_tag.text
                    start_index = text.find(entity)
                    if start_index:
                        end_index = start_index + len(entity)

                        # Replace the entity with the new <a> tag
                        new_link = soup.new_tag('a', href=url)
                        new_link.string = entity

                        # Clear the paragraph tag
                        p_tag.clear()

                        # Append content before the entity, the link, and content after the entity
                        p_tag.append(NavigableString(text[:start_index]))
                        p_tag.append(new_link)
                        p_tag.append(NavigableString(text[end_index:]))
                        print(f"Entity {entity} replaced with anchor text {new_link}")
                        break

    return str(soup)


@app.route('/post/update-anchors', methods=['POST'])
def post_update_anchors():
    # Controlla se i dati sono stati inviati come JSON
    if not request.is_json:
        return jsonify({"error": "Invalid content type. Expected application/json"}), 400

    data = request.get_json()

    # Estrai i dati dal JSON ricevuto
    content = data.get('content')

    # Verifica che sia stato fornito il contenuto
    if not content:
        return jsonify({"error": "Missing 'content'"}), 400

    content = update_anchors(content)

    # Simulazione di salvataggio
    response = {
        "content": content,
        "content_length": len(content)  # Lunghezza del contenuto ricevuto
    }

    return jsonify(response), 200

# @app.route('/get/<post_id>', methods=['GET'])
# def load(post_id):
#     """
#     Load a Post with candidate keywords
#     """
#     v = Tfidf(logger)
#     post_keywords = v.get_post_words(post_id)
#     all_keywords = v.get_keywords()
#     links = []
#     for post_keyword in post_keywords:
#         for keyword_post_id, keyword in all_keywords:
#             if post_keyword == keyword:
#                 links.append({keyword, keyword_post_id})
#
#     return jsonify({'links' : links, 'post_keywords' : post_keywords}), 200


# def init_entities():
#     logger.info('Start init process')
#
#     # Load Wordpress Posts (post_id, post_content)]
#     posts = {}
#     for row in wp.get_wp_posts(from_post_date=settings.WP_QUERY['select_posts_from_date'],
#                                to_post_date=settings.WP_QUERY['select_posts_to_date']):
#         post_id = row[0]
#         post_text = util.clean_html(row[1]).replace('\n', '')
#
#         entities = extract_entities(post_text)
#         # print(f"Text: {post_text}")
#         print(f"Entities extracted from Post ID {post_id}:", entities)
#
#         # Step 2: For each entity, perform semantic search in the other articles
#         # for entity in entities:
#         #     print(f"\nSemantic search for entity: {entity}")
#         #     best_article, score = semantic_search(entity, posts)
#         #     print(f"\n🔹 Best match for entity '{entity}':")
#         #     print(f"   - Article: {best_article}")
#         #     print(f"   - Similarity Score: {score:.4f}")


# def init_tfidf():
#     logger.info('Start init process')
#
#     # Load Wordpress Posts (post_id, post_content)
#     posts = wp.get_wp_id_posts()
#
#     v = Tfidf(logger)
#     data = []
#     for post in posts:
#         text = util.clean_html(post[1])
#         # build a data array for building with vectorizer
#         data.append((post[0], text))
#     v.build_vectorizer(data)
#
#     logger.info('Init process completed')


if __name__ == '__main__':
    logger.info('Application start')

    # Build Vector by import posts
    # init_entities()

    # Users: redazione(2), marco.bianchi(13), francesca.moretti(14)
    posts = wp.get_wp_posts(from_post_date=settings.WP_QUERY['select_posts_from_date'],
                            to_post_date=settings.WP_QUERY['select_posts_to_date'],
                            where="post_author = 2", order='DESC')
    for post in posts:
        post_id = post[0]
        post_content = post[1]
        post_content = update_anchors(post_content)
        print(f"Updating post {post_id} with content: {post_content}")
        wp.wp_update_post_content(post_id, post_content)

    app.run(host=settings.WEB_SETTINGS['host'],
            port=settings.WEB_SETTINGS['port'],
            debug=settings.WEB_SETTINGS['debug'],
            use_reloader=settings.WEB_SETTINGS['use_reloader'])
