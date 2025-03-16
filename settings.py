# Settings

WEB_SETTINGS = {
    'host': 'localhost',
    'port': '5050',
    'debug': True,
    'use_reloader': False
}

LOG_SETTINGS = {
    'level': 'DEBUG',
    'path': 'log',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
}

DB_SETTINGS = {
    'host': 'localhost',
    'user': 'wpseoscan',
    'password': 'password',
    'database': 'wpseoscan',
}

WORK_DIR = 'storage'
OPENAI_SECRET = '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'

WP_QUERY = {
    'select_posts_from_date': '2021-01-23 00:00:00',
    'select_posts_to_date': '2021-12-31 00:00:00',
    'post_author': 2
}

BLACKLIST_ENTITIES = ['iflscience', 'sciencealert', 'interestingengineering']

BASE_URL = 'https://www.scienzenotizie.it'

WP_SETTINGS = {
    'host': 'localhost',
    'user': 'scienzenotizie',
    'password': 'password',
    'database': 'scienzenotizie'
}