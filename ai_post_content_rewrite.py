import random
import re
import time
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright
import requests
from bs4 import BeautifulSoup
import openai
import wp

from settings import WP_QUERY, BASE_URL

def is_invalid(text):
    # Check if it's part of a URL (e.g., www.example.com/path or example.com/path)
    if re.match(r'^(https?://[^\s]+|(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?:/[^\s]*)?)$', text):
        print(f"Invalid text link: {text}")
        return True

    return False


def get_title_with_plsywright(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()  # Creates a new, clean browser context
        page = context.new_page()

        try:
            page.goto(url, timeout=30000)  # Waits up to 30 seconds for the page to load fully
            title = page.title()
            return title
        except Exception as e:
            return {"error": str(e)}
        finally:
            browser.close()


def get_title_and_links(post_id, post_content):
    # Parse the HTML content
    soup = BeautifulSoup(post_content, 'html.parser')

    # Use CSS selector to select all <a> tags within <ul><li>
    p_tag = soup.find('p', string=re.compile(r'\s*Links:\s*'))
    a_list = []
    if p_tag:
        a_list = p_tag.find_all('a')

    # Extract the URLs from the <a> tags
    links = []

    # Check if the URL is valid
    parent_p = None
    for a in a_list:
        if a.has_attr('href'):
            url = a['href']
            description = a.get_text()
            if is_invalid(description):
                title = get_title_with_plsywright(url)
                if title:
                    links.append({'url': url, 'description': title})
                    if parent_p is None:
                        parent_p = a.find_parent('p')



    if parent_p:
        parent_p.extract()

    return links, str(soup)


def add_links_to_post_content(links, html_content):
    return openai.completions(messages=[
            {"role": "system", "content": "Sei un SEO Content Specialist e devi aggiungere dei link a un testo HTML. I link devono essere pertinenti al contenuto ed essere inseriti in modo naturale senza interrompere la lettura."},
            {'role': 'user', 'content': f"Questi sono i link, composti da 'url' (da inserire nell'attributo href) e 'description' che descrive il link: {links}."},
            {'role': 'user', 'content': f"Questo è il testo html che deve essere aggiornato con i link, possibilmente inserendo il link nel testo originale o aggiungendo testo se non si trova il modo migliore secondo SEO: {html_content}."},
            {'role': 'user', 'content': f"Restituisci il testo html modificato senza aggiungere altro."}])


def update_posts():
    print("Fetching WordPress post content...")
    posts = wp.get_wp_posts(from_post_date=WP_QUERY['select_posts_from_date'],
                            to_post_date=WP_QUERY['select_posts_to_date'],
                            where="post_author = 2 AND post_content LIKE '%Links:%'")

    if not posts:
        print("No posts found.")
        return

    print(f"Checking {len(posts)} posts")
    posts_updated = 0
    for post_id, post_content in posts:
        # Remove captions if image URL is valid
        links, new_post_content = get_title_and_links(post_id, post_content)
        if links and new_post_content:
            print(f"Post: {post_id} Links: {links}")
            ai_content = add_links_to_post_content(links, new_post_content)
            if ai_content.startswith("```html"):
                ai_content = ai_content[8:-3]
            if ai_content.startswith("```"):
                ai_content = ai_content[3:-3]
            print(f"Updating post {post_id} with ai content: {ai_content}")
            wp.wp_update_post_content(post_id, ai_content)
            posts_updated += 1
    print(f"{posts_updated} posts updated correctly")


if __name__ == "__main__":
    update_posts()
