import threading 
import time 
import jwt
import datetime
import psycopg2
import psycopg2.extras
from functools import wraps
from flask import Flask , request , jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
api = Flask(__name__)
CORS(
    api,
    resources={r"/*": {"origins": ["http://localhost:5500", "http://127.0.0.1:5500"]}},
    supports_credentials=False,
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)
SECRET_KEY='gnedigeehebdfsbdfbsdbigsidhiruhgu'

DB_CONFIG = dict(
    dbname='instagram_api',
    user='postgres',
    password='password',
    host='localhost',
    port=5432
)

def get_db():
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit=True
    return conn

def create_token(user_id):
    payload={
        "user_id":user_id,
        "exp":datetime.datetime.utcnow()+datetime.timedelta(days=7),
    }
    return jwt.encode(payload,SECRET_KEY,algorithm='HS256')

def token_required(f):
    @wraps(f)
    def decorated(*args,**kwargs):
        auth_header=request.headers.get("Authorization","")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error":"Missing or malformed Authorization header"}) , 401
        
        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token,SECRET_KEY,algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({"error:Invalid token"}),401
        except jwt.InvalidTokenError:
            return jsonify({"error":"Invalid token"}),401
        request.user_id=payload["user_id"]
        return f(*args, **kwargs)
    return decorated

lock=threading.Lock()
latest_event={
    'version':0,
    'type':None,
    'data':None
}


def publish_event(event_type,data):
    with lock:
        latest_event['version']+=1
        latest_event['type']=event_type
        latest_event['data']=data

def wait_for_new_event(since_version,timeout=25):
    start = time.time()
    while time.time() - start < timeout:
        with lock:
            if latest_event['version']>since_version:
                return dict(latest_event)
        time.sleep(0.5)
    return None

@api.route("/signup",methods=["POST"])
def signup():
    data=request.get_json()
    username=data.get("username")
    email=data.get("email")
    password=data.get("password")
    if not all([username,email,password]):
        return jsonify({'error':"username,email,password are required"}),400
    password_hash = generate_password_hash(password)
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cur.execute(
            """
            INSERT INTO users (username,email,password_hash)
            VALUES (%s,%s,%s) RETURNING user_id,username,email
            """ ,
            (username,email,password_hash),
        )
        user=cur.fetchone()
    except psycopg2.errors.UniqueViolation:
        return jsonify({'error':'username or email already taken'}),409
    finally:
        cur.close()
        conn.close()
    token = create_token(user['user_id'])
    return jsonify({'user':user,'token':token}),201

@api.route("/login",methods=["POST"])
def login():
    data=request.get_json()
    username=data.get("usernamme")
    password=data.get("password")

    conn = get_db()
    cur =  conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM users WHERE username = %s",(username,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user or not check_password_hash(user["password_hash"],password):
        return jsonify({"error":"Invalid username or password"}),401
    token = create_token(user['user_id'])
    return jsonify({'token':token}),200

# ---------- Profile routes ----------

@api.route("/users/<int:user_id>",methods=["GET"])
def get_profile(user_id):
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        "SELECT user_id, username, email, bio, created_at FROM users WHERE user_id = %s",
        (user_id,),
    )
    user = cur.fetchone()
    cur.close()
    conn.close()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(user), 200

@api.route("/users/<int:user_id>/posts", methods=["GET"])
def get_user_posts(user_id):
    limit = int(request.args.get('limit', 20))
    offset = int(request.args.get('offset', 0))

    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        """
        SELECT posts.post_id, posts.caption, posts.image_url, posts.created_at,
               users.username, COUNT(likes.user_id) AS like_count
        FROM posts
        JOIN users ON posts.user_id = users.user_id
        LEFT JOIN likes ON posts.post_id = likes.post_id
        WHERE posts.user_id = %s
        GROUP BY posts.post_id, posts.caption, posts.image_url, posts.created_at,
                 users.username
        ORDER BY posts.created_at DESC
        LIMIT %s OFFSET %s
        """,
        (user_id, limit, offset)
    )
    posts = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([post_to_jsonable(p) for p in posts]), 200

@api.route("/users/me", methods=["PUT"])
@token_required
def update_profile():
    data = request.get_json()
    bio = data.get("bio")

    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        """
        UPDATE users SET bio = %s WHERE user_id = %s
        RETURNING user_id, username, bio
        """,
        (bio, request.user_id),
    )
    user = cur.fetchone()
    cur.close()
    conn.close()
    return jsonify(user), 200


#--------Helper functions-----
def post_to_jsonable(post):
    # psycopg2 returns datetime objects; JSON needs them as strings
    post = dict(post)
    post["created_at"] = str(post["created_at"])
    return post
#---------Post routes--------

@api.route('/posts',methods=['POST'])
@token_required
def create_post():
    data = request.get_json()
    caption = data.get('caption')
    image_url = data.get('image_url')
    if not image_url:
        return jsonify({"error": "image_url is required"}), 400
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
    INSERT INTO posts (user_id,caption,image_url)
    VALUES (%s,%s,%s) RETURNING post_id , user_id , caption , image_url , created_at
    """,(request.user_id,caption,image_url)
    )

    post = cur.fetchone()
    cur.close()
    conn.close()

    publish_event('new_post',post_to_jsonable(post))
    return jsonify(post),201


@api.route("/feed", methods=["GET"])
def get_feed():
    limit = int(request.args.get('limit', 10))
    offset = int(request.args.get("offset", 0))

    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        """
        SELECT posts.post_id, posts.caption, posts.image_url, posts.created_at,
               users.username, COUNT(likes.user_id) AS like_count
        FROM posts
        JOIN users ON posts.user_id = users.user_id
        LEFT JOIN likes ON posts.post_id = likes.post_id
        GROUP BY posts.post_id, posts.caption, posts.image_url, posts.created_at,
                 users.username
        ORDER BY posts.created_at DESC
        LIMIT %s OFFSET %s
        """,
        (limit, offset)
    )

    posts = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify([post_to_jsonable(p) for p in posts]), 200

# ---------- Like routes ----------

@api.route("/posts/<int:post_id>/like", methods=["POST"])
@token_required
def like_post(post_id):
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cur.execute(
            "INSERT INTO likes (user_id, post_id) VALUES (%s, %s)",
            (request.user_id, post_id),
        )
    except psycopg2.errors.UniqueViolation:
        cur.close()
        conn.close()
        return jsonify({"error": "Already liked"}), 409

    cur.execute("SELECT COUNT(*) FROM likes WHERE post_id = %s", (post_id,))
    like_count = cur.fetchone()["count"]
    cur.close()
    conn.close()

    publish_event("new_like", {"post_id": post_id, "like_count": like_count})
    return jsonify({"post_id": post_id, "like_count": like_count}), 201

# ---------- Long polling endpoint ----------

@api.route("/events/poll", methods=["GET"])
def poll_events():
    since_version = int(request.args.get("since", 0))
    event = wait_for_new_event(since_version)
    if event is None:
        # Timed out — nothing happened. Client should immediately call /events/poll again.
        return jsonify({"timeout": True, "version": since_version}), 204
    return jsonify(event), 200


if __name__ == "__main__":
    api.run(debug=True, threaded=True)   # threaded=True is REQUIRED for long polling to work!