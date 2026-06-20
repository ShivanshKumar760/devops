from flask import Flask , jsonify , request
from psycopg2.extras import RealDictCursor
from db import get_connection , release_connection

app = Flask(__name__)

@app.route('/users', methods=['GET'])
def get_users():
    conn = get_connection()
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT user_id,username,full_name,bio FROM users ORDER BY user_id")
        users= cursor.fetchall()
        cursor.close()
        return jsonify(users)
    finally:
        release_connection(conn)

@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    conn = get_connection()
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT user_id , username , full_name , bio FROM users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        cursor.close()
        if user is None:
            return jsonify({"error": "User not found"}), 404
        return jsonify(user)
    finally:
        release_connection(conn)


@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    if not data or 'username' not in data or 'email' not in data:
        return jsonify({"error": "Invalid input"}), 400
    conn = get_connection()
    try :
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            "INSERT INTO users (username, email, full_name, bio) VALUES (%s, %s, %s, %s) RETURNING user_id, username, full_name, bio",
            (data['username'], data['email'], data.get('full_name'), data.get('bio'))
        )
        new_user = cursor.fetchone()
        conn.commit()
        cursor.close()
        return jsonify(new_user), 201
    finally:
        release_connection(conn)

@app.route("/posts", methods=["GET"])
def get_posts():
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """
            SELECT posts.post_id, posts.caption, posts.created_at, users.username
            FROM posts
            JOIN users ON posts.user_id = users.user_id
            ORDER BY posts.created_at DESC;
            """
        )
        posts = cur.fetchall()
        cur.close()
        return jsonify(posts), 200
    finally:
        release_connection(conn)