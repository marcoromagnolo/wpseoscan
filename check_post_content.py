import re
import wp
import requests

from settings import WP_SETTINGS, WP_QUERY

# Regular expression to extract image URLs
IMAGE_REGEX = r'<img\s+[^>]*src=["\'](https?://[^"\']+)["\']'

LINK_REGEX = r'<a\s+[^>]*href=["\'](https?://[^"\']+)["\']'

IFRAME_REGEX = r'<iframe\s+[^>]*src=["\'](https?://[^"\']+)["\']'

def extract_image_urls(post_content):
    """Extracts image URLs from post_content using regex."""
    return re.findall(IMAGE_REGEX, post_content)


def extract_link_urls(post_content):
    """Extracts image URLs from post_content using regex."""
    return re.findall(LINK_REGEX, post_content)


def extract_iframe_urls(post_content):
    """Extracts image URLs from post_content using regex."""
    return re.findall(IFRAME_REGEX, post_content)


def check_url_status(url, allow_redirects):
    """Checks the HTTP status of a URL."""
    response = requests.head(url, allow_redirects=allow_redirects, timeout=5)
    response.raise_for_status()



def main():
    print("Fetching WordPress post content...")
    posts = wp.get_wp_posts(from_post_date=WP_QUERY['select_posts_from_date'],
                            to_post_date=WP_QUERY['select_posts_to_date'])

    if not posts:
        print("No posts found.")
        return

    image_urls = set()  # To avoid duplicate URLs
    link_urls = set()
    iframe_urls = set()
    for post_id, content in posts:
        for url in extract_image_urls(content):
            image_urls.add((post_id, url))
        for url in extract_link_urls(content):
            link_urls.add((post_id, url))
        for url in extract_iframe_urls(content):
            iframe_urls.add((post_id, url))

    print(f"Checking {len(image_urls)} image URLs...")

    for post_id, url in image_urls:
        try:
            check_url_status(url, False)
        except Exception as e:
            print(f"Post ID: {post_id} | img src: {url} | Error: {e}")

    print(f"Checking {len(link_urls)} link URLs...")

    for post_id, url in link_urls:
        try:
            check_url_status(url, True)
        except Exception as e:
            print(f"Post ID: {post_id} | link href: {url} | Error: {e}")

    print(f"Checking {len(iframe_urls)} iframe URLs...")

    for post_id, url in iframe_urls:
        try:
            check_url_status(url, True)
        except Exception as e:
            print(f"Post ID: {post_id} | iframe src: {url} | Error: {e}")


if __name__ == "__main__":
    main()
