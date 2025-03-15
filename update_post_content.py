import os
import re
from asyncio import timeout
from inspect import isframe

import wp
import requests

from settings import WP_QUERY, BASE_URL


def update_urls(content):
    # Define the list of patterns to replace
    patterns = [
        r'http://www\.scienzenotizie\.it',
        r'http://scienzenotizie\.it',
        r'https://scienzenotizie\.it'
    ]

    # Replace all matching URLs with the correct URL
    for pattern in patterns:
        content = re.sub(pattern, BASE_URL, content)

    return content


# Function to check if the image URL is valid (not 404)
def invalid_url(url, check_local=False):
    if check_local and not url.startswith(BASE_URL):
        print(f"Url is not local: {url}")
        return True

    try:
        response = requests.head(url, allow_redirects=True, timeout=5)
        # If the URL responds with status code 200, it's valid
        if response.status_code == 200:
            return False
        elif response.status_code == 404:
            print(f"Error at URL: {url} with code: {response.status_code}")
            return True
    except Exception as e:
        print(f"Invalid endpoint - Error checking URL: {url} - {e}")
        return True


# Function to remove caption blocks based on image URL validity
def is_duplicate_image(featured_image, img_url):
    featured_image_name, _ = os.path.splitext(featured_image)

    if featured_image == img_url or img_url.startswith(featured_image_name) or img_url.startswith(featured_image_name):
        print(f"Image are duplicated: {featured_image} {img_url}")
        return True
    return False


def update_iframe_src(post_id, post_content):
    # Regular expression pattern to find all caption shortcodes
    iframe_pattern = r'<iframe[^>]*[/]?>.*?</iframe>|<iframe[^>]*/?>'

    # Find all the caption blocks
    iframes = re.findall(iframe_pattern, post_content, re.DOTALL | re.IGNORECASE)
    update = False
    if iframes:
        # Loop through each caption block to check if the image URL is valid
        for iframe in iframes:
            # Extract the image URL (src) from the caption block using regex
            iframe_src_pattern = r'<iframe[^>]+src=["\']?([^"\'> ]+)[^>]*[/]?>'
            isframe_url_match = re.search(iframe_src_pattern, iframe)

            if isframe_url_match:
                url = isframe_url_match.group(1)
                if invalid_url(url):
                    print(f"Post ID: {post_id} remove <iframe> with URL: {url}")
                    post_content = post_content.replace(iframe, '')
                    update = True

    return update, post_content


def update_a_href(post_id, post_content):
    # Regular expression pattern to find all caption shortcodes
    a_pattern = r'<a[^>]*>.*?</a>'

    # Find all the caption blocks
    links = re.findall(a_pattern, post_content, re.DOTALL)
    update = False
    if links:
        # Loop through each caption block to check if the image URL is valid
        for link in links:
            # Extract the image URL (src) from the caption block using regex
            link_href_pattern = r'<a[^>]+href=["\'](.*?)["\']'
            link_url_match = re.search(link_href_pattern, link)

            if link_url_match:
                url = link_url_match.group(1)
                if invalid_url(url):
                    print(f"Post ID: {post_id} remove <a> with URL: {url}")
                    post_content = post_content.replace(link, '')
                    update = True

    return update, post_content


def update_img_src(post_id, post_content):
    # Regular expression pattern to find all caption shortcodes
    img_pattern = r'(<img[^>]+>)'

    # Find all the caption blocks
    imgs = re.findall(img_pattern, post_content, re.DOTALL)
    update = False
    if imgs:
        # Loop through each caption block to check if the image URL is valid
        for img in imgs:
            # Extract the image URL (src) from the caption block using regex
            img_url_pattern = r'<img[^>]+src="([^"]+)"'
            img_url_match = re.search(img_url_pattern, img)

            if img_url_match:
                url = img_url_match.group(1)

                if invalid_url(url, True):

                    url_no_ext, ext = os.path.splitext(url)
                    new_url = url_no_ext[:-2] + ext

                    featured_images = wp.get_wp_post_featured_image(post_id)
                    for featured_image in featured_images:
                        if featured_image[0] == new_url:
                            print(f"Post ID: {post_id} duplicated <img> with URL: {url}")
                            post_content = post_content.replace(img, '')
                            update = True

                    if update:
                        continue

                    print(f"Invalid image URL try with: {new_url}")
                    if invalid_url(new_url, True):
                        print(f"Post ID: {post_id} remove <img> with URL: {url}")
                        post_content = post_content.replace(img, '')
                    else:
                        print(f"Post ID: {post_id} update <img> src with URL: {new_url}")
                        new_img = img.replace(url, new_url)
                        post_content = post_content.replace(img, new_img)
                    update = True

    return update, post_content


def update_custom_tag(post_id, post_content):
    # Regular expression pattern to find all caption shortcodes
    pattern = re.compile(
            r'<p>Font.*?<a href="([^"]+)">.*?</a>.*?</p>',

        re.DOTALL | re.IGNORECASE
    )

    # Replacement Template
    replacement_template = r'<p><a href="\1">Fonte dell\'articolo.</a></p>'

    # Find all the caption blocks
    new_content = re.sub(pattern, replacement_template, post_content)
    new_content = new_content.replace("\\", "")
    update = False
    if new_content != post_content:
        print(f"Post ID: {post_id} update fonte.")
        update = True

    return update, new_content


def update_figure_tags(post_id, post_content):
    # Regular expression pattern to find all caption shortcodes
    caption_pattern = r'<figure.*?>(.*?)</figure>'

    # Find all the caption blocks
    captions = re.findall(caption_pattern, post_content, re.DOTALL)
    update = False
    if captions:
        # Loop through each caption block to check if the image URL is valid
        for caption in captions:
            # Extract the image URL (src) from the caption block using regex
            img_url_pattern = r'<img[^>]+src="([^"]+)"'
            img_url_match = re.search(img_url_pattern, caption)

            if img_url_match:
                img_url = img_url_match.group(1)
                featured_images = wp.get_wp_post_featured_image(post_id)
                for featured_image in featured_images:
                    if is_duplicate_image(featured_image[0], img_url) or invalid_url(img_url, True):
                        print(f"Post ID: {post_id} Removing <figcaption> with image: {img_url}")
                        # If the image URL is valid, remove the entire caption block from post_content
                        update = True
                        post_content = re.sub(r'<figure.*?>' + re.escape(caption) + r'</figure>', '', post_content, flags=re.DOTALL)


    return update, post_content


def update_img_tags():
    print("Fetching WordPress post content...")
    posts = wp.get_wp_posts(from_post_date=WP_QUERY['select_posts_from_date'],
                            to_post_date=WP_QUERY['select_posts_to_date'],
                            where="post_content LIKE '%<img %'")

    if not posts:
        print("No posts found.")
        return

    print(f"Checking {len(posts)} image URLs...")
    for post_id, post_content in posts:
        # Remove captions if image URL is valid
        update, cleaned_content = update_img_src(post_id, post_content)
        if update:
            print(f"Updating post {post_id} with cleaned content")
            wp.wp_update_post_content(post_id, cleaned_content)


def update_a_tags():
    print("Fetching WordPress post content...")
    posts = wp.get_wp_posts(from_post_date=WP_QUERY['select_posts_from_date'],
                            to_post_date=WP_QUERY['select_posts_to_date'],
                            where="post_content LIKE '%<a %'")

    if not posts:
        print("No posts found.")
        return

    print(f"Checking {len(posts)} <a> link URLs...")
    for post_id, post_content in posts:
        # Remove captions if image URL is valid
        update, cleaned_content = update_a_href(post_id, post_content)
        if update:
            print(f"Updating post {post_id} with cleaned content")
            wp.wp_update_post_content(post_id, cleaned_content)


def update_iframe_tags():
    print("Fetching WordPress post content...")
    posts = wp.get_wp_posts(from_post_date=WP_QUERY['select_posts_from_date'],
                            to_post_date=WP_QUERY['select_posts_to_date'],
                            where="post_content LIKE '%<iframe %'")

    if not posts:
        print("No posts found.")
        return

    print(f"Checking {len(posts)} <iframe> src URLs...")
    for post_id, post_content in posts:
        # Remove captions if image URL is valid
        update, cleaned_content = update_iframe_src(post_id, post_content)
        if update:
            print(f"Updating post {post_id} with cleaned content")
            wp.wp_update_post_content(post_id, cleaned_content)


def update_custom_html():
    print("Fetching WordPress post content...")
    posts = wp.get_wp_posts(from_post_date=WP_QUERY['select_posts_from_date'],
                            to_post_date=WP_QUERY['select_posts_to_date'],
                            where="(post_content LIKE '%>http://%' OR post_content LIKE '%>https://%')")

    if not posts:
        print("No posts found.")
        return

    print(f"Checking {len(posts)} unformatted URLs...")
    for post_id, post_content in posts:
        # Remove captions if image URL is valid
        update, cleaned_content = update_custom_tag(post_id, post_content)
        if update:
            print(f"Updating post {post_id} with cleaned content")
            wp.wp_update_post_content(post_id, cleaned_content)


if __name__ == "__main__":
    update_custom_html()
