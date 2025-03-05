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


def get_wp_posts(from_post_date='1970-01-01 00:00:00', to_post_date=datetime.now(), status='publish', post_type='post'):
    db_connection = open_connection()
    db_cursor = db_connection.cursor()
    select_query = f"""
        SELECT id, post_content from wp_posts 
        WHERE post_type = '{post_type}' AND post_status = '{status}'
        AND post_date BETWEEN %s AND %s
        ORDER BY id
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

