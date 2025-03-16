import mysql.connector
from settings import WP_SETTINGS
from datetime import datetime
import json


def open_connection():
    db_connection = mysql.connector.connect(**WP_SETTINGS)
    return db_connection


def get_last_insert_id(db_cursor):
    db_cursor.execute("SELECT LAST_INSERT_ID()")
    return db_cursor.fetchone()[0]


def get_order_by(orders):
    if orders:
        return f"ORDER BY {orders}"
    return ""


def get_wp_posts(from_post_date='1970-01-01 00:00:00', to_post_date=datetime.now(), status='publish', post_type='post',
                 where=None, order='ASC', limit=None):
    db_connection = open_connection()
    db_cursor = db_connection.cursor()

    if where:
        where = f"AND {where}"
    else:
        where = ''

    if limit:
        limit = f"LIMIT {limit}"
    else:
        limit = ''

    select_query = f"""
        SELECT id, post_content from wp_posts 
        WHERE post_type = '{post_type}' AND post_status = '{status}'
        AND post_date BETWEEN %s AND %s {where} ORDER BY id {limit} {order}
    """

    try:
        db_cursor.execute(select_query, (from_post_date, to_post_date))
        return db_cursor.fetchall()
    finally:
        db_cursor.close()
        db_connection.close()


def get_wp_id_posts(post_date='2025-01-01 00:00:00'):
    db_connection = open_connection()
    db_cursor = db_connection.cursor()
    select_query = f"""
        SELECT id, post_content from wp_posts 
        WHERE post_type = 'post' AND post_status = 'publish'
        AND post_date > %s
    """

    try:
        db_cursor.execute(select_query, (post_date,))
        return db_cursor.fetchall()
    finally:
        db_cursor.close()
        db_connection.close()


def get_wp_post_featured_image(post_id):
    db_connection = open_connection()
    db_cursor = db_connection.cursor()
    select_query = f"""
                    SELECT p.guid 
                    FROM wp_postmeta pm
                    LEFT JOIN wp_posts p ON p.ID = pm.meta_value
                    WHERE post_id = %s
                      AND meta_key = '_thumbnail_id'
                    GROUP BY p.guid
                """

    try:
        db_cursor.execute(select_query, (post_id,))
        return db_cursor.fetchall()
    finally:
        db_cursor.close()
        db_connection.close()


def wp_update_post_content(post_id, cleaned_content):
    db_connection = open_connection()
    db_cursor = db_connection.cursor()
    update_query = f"""
        UPDATE wp_posts
        SET post_content = %s
        WHERE id = %s
    """

    try:
        db_cursor.execute(update_query, (cleaned_content, post_id))
        db_connection.commit()
    finally:
        db_cursor.close()
        db_connection.close()


def search_wp_post_titles(entity, not_id=None):
    db_connection = open_connection()
    db_cursor = db_connection.cursor()
    select_query = f"""
            SELECT id, post_title from wp_posts 
            WHERE post_type = 'post' AND post_status = 'publish' 
            AND post_title LIKE %s order by ID desc limit 10
        """

    try:
        db_cursor.execute(select_query, (f"%{entity}%", ))
        posts = {}
        for row in db_cursor.fetchall():
            if not_id and row[0] == not_id:
                continue
            posts[row[0]] = row[1]
        return posts
    finally:
        db_cursor.close()
        db_connection.close()


def get_post_permalink(post_id):
    """ Select the permalink for a post """
    db_connection = open_connection()
    db_cursor = db_connection.cursor()
    select_query = """
            SELECT 
                CONCAT(
                    '/', 
                    DATE_FORMAT(post_date, '%Y/%m/%d/'), 
                    post_name, 
                    '-', 
                    LPAD(SECOND(post_date), 2, '0'), 
                    ID
                )
            FROM wp_posts
            WHERE post_type = 'post'
            AND post_status = 'publish'
            WHERE id = %s
        """

    try:
        db_cursor.execute(select_query, (post_id,))
        row = db_cursor.fetchone()
        if row:
            return row[0]
    finally:
        db_cursor.close()
        db_connection.close()


def get_post_guid(post_id):
    db_connection = open_connection()
    db_cursor = db_connection.cursor()
    select_query = """
            SELECT guid from wp_posts 
            WHERE id = %s
        """

    try:
        db_cursor.execute(select_query, (post_id,))
        row = db_cursor.fetchone()
        if row:
            return row[0]
    finally:
        db_cursor.close()
        db_connection.close()