from flask import Flask
import psycopg2
import psycopg2.extras
import redis
import json
import os
from dotenv import load_dotenv

load_dotenv()  # reads .env from the same folder

app = Flask(__name__)

def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )

def get_redis():
    return redis.Redis(host=os.getenv('REDIS_HOST'), port=int(os.getenv('REDIS_PORT')), db=0)

@app.route('/create-cache', methods=['POST'])
def create_cache():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT n.id, n.title, n.content, c.name as category
        FROM newspaper_news n
        LEFT JOIN newspaper_category c ON n.category_id = c.id
        ORDER BY n.created_at DESC
    """)
    news_rows = cur.fetchall()
    cur.close()
    conn.close()

    # Convert rows to list of dicts and store in Redis as JSON
    news_list = [dict(row) for row in news_rows]
    r = get_redis()
    r.set('homepage_news', json.dumps(news_list))
    return f"Cache created with {len(news_list)} news items."

@app.route('/expire-cache', methods=['POST'])
def expire_cache():
    r = get_redis()
    r.delete('homepage_news')
    return "Cache expired (key deleted)."

if __name__ == '__main__':
    app.run(port=5000, debug=True)