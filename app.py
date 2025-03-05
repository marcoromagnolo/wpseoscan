import werkzeug.exceptions
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import wp
import settings
import pidman
import logg
import util
from entity import semantic_search, extract_entities
from tfidf import Tfidf


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


@app.route('/get/<post_id>', methods=['GET'])
def load(post_id):
    """
    Load a Post with candidate keywords
    """
    v = Tfidf(logger)
    post_keywords = v.get_post_words(post_id)
    all_keywords = v.get_keywords()
    links = []
    for post_keyword in post_keywords:
        for keyword_post_id, keyword in all_keywords:
            if post_keyword == keyword:
                links.append({keyword, keyword_post_id})

    return jsonify({'links' : links, 'post_keywords' : post_keywords}), 200


def init_entities():
    logger.info('Start init process')

    # Load Wordpress Posts (post_id, post_content)]
    posts = {}
    for row in wp.get_wp_posts():
        posts[row[0]] = util.clean_html(row[1])

    # Step 1: Extract entities from the first article
    _, search_post = posts.popitem()
    entities = extract_entities(search_post)
    print("Entities extracted from Article 1:", entities)

    # Step 2: For each entity, perform semantic search in the other articles
    for entity in entities:
        print(f"\nSemantic search for entity: {entity}")
        best_article, score = semantic_search(entity, posts)
        print(f"\n🔹 Best match for entity '{entity}':")
        print(f"   - Article: {best_article}")
        print(f"   - Similarity Score: {score:.4f}")


def init_tfidf():
    logger.info('Start init process')

    # Load Wordpress Posts (post_id, post_content)
    posts = wp.get_wp_id_posts()

    v = Tfidf(logger)
    data = []
    for post in posts:
        text = util.clean_html(post[1])
        # build a data array for building with vectorizer
        data.append((post[0], text))
    v.build_vectorizer(data)

    logger.info('Init process completed')


if __name__ == '__main__':
    logger.info('Application start')

    # Build Vector by import posts
    init_entities()

    app.run(host=settings.WEB_SETTINGS['host'],
            port=settings.WEB_SETTINGS['port'],
            debug=settings.WEB_SETTINGS['debug'],
            use_reloader=settings.WEB_SETTINGS['use_reloader'])
