import os
import re
import wp
import requests

from settings import WP_SETTINGS, WP_QUERY


def update_urls(content):
    # Define the list of patterns to replace
    patterns = [
        r'http://www\.scienzenotizie\.it',
        r'http://scienzenotizie\.it',
        r'https://scienzenotizie\.it'
    ]

    # Replace all matching URLs with the correct URL
    for pattern in patterns:
        content = re.sub(pattern, 'https://www.scienzenotizie.it', content)

    return content

# Function to check if the image URL is valid (not 404)
def invalid_image_url(url):
    if not url.startswith("https://www.scienzenotizie.it"):
        print(f"Image is not local: {url}")
        return True

    try:
        response = requests.head(url, allow_redirects=True)
        # If the URL responds with status code 200, it's valid
        if response.status_code == 200:
            return False
        else:
            print(f"Error image not found at URL: {url}")
            return True
    except requests.exceptions.RequestException as e:
        print(f"Invalid Image - Error checking URL: {url} - {e}")
        return False


# Function to remove caption blocks based on image URL validity
def is_duplicate_image(featured_image, img_url):
    featured_image_name, _ = os.path.splitext(featured_image)

    if featured_image == img_url or img_url.startswith(featured_image_name) or img_url.startswith(featured_image_name):
        print(f"Image are duplicated: {featured_image} {img_url}")
        return True
    return False

def remove_caption_if_valid(post_id, post_content):
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
                    if is_duplicate_image(featured_image[0], img_url) or invalid_image_url(img_url):
                        print(f"Post ID: {post_id} Removing <figcaption> with image: {img_url}")
                        # If the image URL is valid, remove the entire caption block from post_content
                        update = True
                        post_content = re.sub(r'<figure.*?>' + re.escape(caption) + r'</figure>', '', post_content, flags=re.DOTALL)


    return update, post_content


def remove_captions():
    print("Fetching WordPress post content...")
    posts = wp.get_wp_posts(from_post_date=WP_QUERY['select_posts_from_date'],
                            to_post_date=WP_QUERY['select_posts_to_date'],
                            where="post_content LIKE '%<figure%'")

    if not posts:
        print("No posts found.")
        return

    print(f"Checking {len(posts)} image URLs...")
    for post_id, post_content in posts:
        # Remove captions if image URL is valid
        update, cleaned_content = remove_caption_if_valid(post_id, post_content)
        if update:
            print(f"Updating post {post_id} with cleaned content")
            wp.get_wp_update_post_content(post_id, cleaned_content)



if __name__ == "__main__":
    remove_captions()
