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



@app.route("/posts/<int:post_id>/likes", methods=["POST"])
def like_post(post_id):
    data = request.get_json()
    if not data or 'user_id' not in data:
        return jsonify({"error": "Invalid input"}), 400
    conn = get_connection()
    try :
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "INSERT INTO likes (user_id, post_id) VALUES (%s, %s) ON CONFLICT DO NOTHING RETURNING user_id, post_id;",
            (data["user_id"], post_id),
        )

        result = cur.fetchone()
        conn.commit()
        cur.close()
        if result is None:
            return jsonify({"message": "Already liked"}), 200
        return jsonify(result),201
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        release_connection(conn)


@app.route("/posts/<int:post_id>/likes/<int:user_id>", methods=["DELETE"])
def unlike_post(post_id, user_id):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM likes WHERE post_id = %s AND user_id = %s;", (post_id, user_id))
        deleted = cur.rowcount
        conn.commit()
        cur.close()
        if deleted == 0:
            return jsonify({"error": "Like not found"}), 404
        return "", 204
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        release_connection(conn)

