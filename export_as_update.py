import mysql.connector

# Database credentials (modify these)
DB_HOST = "localhost"
DB_USER = "scienzenotizie"
DB_PASSWORD = "password"
DB_NAME = "scienzenotizie"

# Output file for UPDATE statements
OUTPUT_FILE = "update_wp_posts.sql"

try:
    # Connect to the database
    connection = mysql.connector.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME
    )
    cursor = connection.cursor()

    # Select post ID and post_content where <img> exists
    query = """
                SELECT id, post_content FROM wp_posts
                WHERE post_type='post' AND
                (post_content LIKE '%http://scienzenotizie.it%' OR 
                post_content LIKE '%https://scienzenotizie.it%' OR 
                post_content LIKE '%http://www.scienzenotizie.it%')
            """
    cursor.execute(query)
    posts = cursor.fetchall()

    # Open file to write UPDATE statements
    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        for post_id, post_content in posts:
            # Escape single quotes in post_content for SQL compatibility
            escaped_content = post_content.replace("'", "''")

            # Create the UPDATE statement
            update_query = f"UPDATE wp_posts SET post_content = '{escaped_content}' WHERE ID = {post_id};\n"

            # Write to file
            file.write(update_query)

    print(f"✅ SQL update script generated: {OUTPUT_FILE}")

except mysql.connector.Error as e:
    print(f"❌ Database error: {e}")

finally:
    if 'cursor' in locals():
        cursor.close()
    if 'connection' in locals() and connection.is_connected():
        connection.close()
