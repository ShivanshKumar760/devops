import os
from flask import Flask, request , jsonify
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
PORT=os.getenv('PORT', 5000)

def get_conn():
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'postgres-service'),
        port=int(os.getenv('DB_PORT', 5432)),
        dbname=os.getenv('DB_NAME', 'appdb'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'postgres'),
    )

def init_db():
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id         SERIAL PRIMARY KEY,
                name       TEXT NOT NULL,
                value      TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)

    conn.commit()
    conn.close()
    print('DB initialised')


@app.route("/post", methods=["POST"])
def post_item():
    data = request.get_json(force=True)
    name = data.get("name")
    value = data.get("value")

    if not name:
        return jsonify({"error": "name is required"}), 400
    
    conn = get_conn()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            "INSERT INTO items (name, value) VALUES (%s, %s) RETURNING *",
            (name, value)
        )
        row = cur.fetchone()
    conn.commit()
    conn.close()
    return jsonify(dict(row)), 201


@app.route('/fetch', methods=['GET'])
def fetch_items():
    conn = get_conn()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute('SELECT * FROM items ORDER BY created_at DESC')
        rows = cur.fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=PORT, debug=False)