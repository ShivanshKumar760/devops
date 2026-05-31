# import os , json , time , threading
# from datetime import datetime 

# import pika #for rabbitmq
# import psycopg2 #for postgresql
# import psycopg2.pool #for connection pooling
# from flask import Flask , request , jsonify , redirect
# from flask_cors import CORS
# from nanoid import generate
# from dotenv import load_dotenv 


# load_dotenv()

# app=Flask(__name__)
# CORS(app)


# # ─── Config ─────────────────────────────────────────────────────────────────
# PG_HOST   = os.getenv("PG_HOST", "postgres")
# PG_DB     = os.getenv("PG_DB",   "urlshortener")
# PG_USER   = os.getenv("PG_USER", "postgres")
# PG_PASS   = os.getenv("PG_PASSWORD", "postgres")
# RABBIT_URL = os.getenv("RABBIT_URL", "amqp://guest:guest@rabbitmq:5672")
# EXCHANGE  = "url.events"
# BASE_URL  = os.getenv("BASE_URL", "http://localhost:5000")


# #------- PostgreSQL connection pool ──────────────────────────────────────────────
# def make_pool(retries = 10):
#     for i in range(retries):
#         try:
#             pool = psycopg2.pool.ThreadedConnectionPool(
#                 1, 10,
#                 host=PG_HOST, dbname=PG_DB,
#                 user=PG_USER, password=PG_PASS
#             )
#             print("[DB] Connected")
#             return pool
#         except Exception as e:
#             print(f"[DB] Attempt {i+1} failed: {e}")
#             time.sleep(3)
#     raise RuntimeError("Cannot connect to PostgreSQL")

# db_pool=make_pool()

# def get_conn():
#     return db_pool.getconn()

# def put_conn(conn):
#     db_pool.putconn(conn)

# #-------DB Init -----------------------------------------------------------------------
# def init_db():
#     conn = get_conn()
#     try:
#         with conn.cursor() as cur:
#             cur.execute("""
#                 CREATE TABLE IF NOT EXISTS urls (
#                     id          SERIAL PRIMARY KEY,
#                     short_code  VARCHAR(20) UNIQUE NOT NULL,
#                     original_url TEXT NOT NULL,
#                     created_at  TIMESTAMP DEFAULT NOW()
#                 );
#                 CREATE TABLE IF NOT EXISTS analytics (
#                     id          SERIAL PRIMARY KEY,
#                     short_code  VARCHAR(20) NOT NULL,
#                     ip_address  VARCHAR(50),
#                     user_agent  TEXT,
#                     visited_at  TIMESTAMP DEFAULT NOW()
#                 );
#             """)
#             conn.commit()
#             print("[DB] Tables ready")
#     finally:
#         put_conn(conn)
# # ─── RabbitMQ Publisher ──────────────────────────────────────────────────────
# rabbit_channel = None
# rabbit_lock = threading.Lock()

# def connect_rabbit(retries=10):
#     global rabbit_channel
#     for i in range(retries):
#         try:
#             params = pika.URLParameters(RABBIT_URL)
#             connection = pika.BlockingConnection(params)
#             ch = connection.channel()
#             ch.exchange_declare(exchange=EXCHANGE,exchange_type="fanout",durable=True)
#             rabbit_channel = ch
#             print("[RabbitMQ] Connected")
#             return
#         except Exception as e:
#             print(f"[RabbitMQ] Attempt {i+1} failed {e}")
#             time.sleep(3)
#     print("[RabbitMQ] WARNING: Could not connect - events will be skipped")

# def publish_event(payload: dict):
#     global rabbit_channel
#     with rabbit_lock:
#         try:
#             if rabbit_channel:
#                 rabbit_channel.basic_publish(
#                     exchange=EXCHANGE,
#                     routing_key=" ",
#                     body = json.dumps(payload),
#                     properties=pika.BasicProperties(delivery_mode=2)
#                 )
#         except Exception as e:
#             print(f"[RabbitMQ] Publish failed: {e}")

# # ─── Routes (using @app.route decorator) ────────────────────────────────────
# @app.route("/",methods=["GET"])
# def index():
#     return jsonify({"message": "URL Shortener API is running"})

# @app.route("/short",methods=["POST"])
# def shorten():
#     """
#     POST /short
#     Body: {"url":"https://example.com"}
#     Returns :{
#         "short_code":"aB3x9k",
#         "short_url":"http://host/aB3x9K"
#     }
#     """

#     data = request.get_json(silent=True) or {}
#     url = data.get("url")
#     if not url:
#         return jsonify({
#             "error": "url is required"
#         })
    
#     short_code = generate(size=6)
#     #1.write to postgres synchronously 
#     conn = get_conn()
#     try:
#         with conn.cursor() as cur:
#             cur.execute(
#                 'INSERT INTO urls (short_code , original_url) VALUES (%s,%s)',
#                 (short_code,url)
#             )
#             conn.commit()
#     finally:
#         put_conn(conn)

#         # 2. Broadcast fanout event
#     publish_event({
#         "type": "URL_CREATED",
#         "short_code": short_code,
#         "original_url": url,
#         "ip": request.remote_addr,
#         "user_agent": request.headers.get("User-Agent", ""),
#         "timestamp": datetime.utcnow().isoformat(),
#     })
 
#     return jsonify({
#         "short_code": short_code,
#         "short_url":  f"{BASE_URL}/{short_code}"
#     }), 201

# @app.route("/<string:code>", methods=["GET"])
# def redirect_short(code):
#     """GET /<code> — look up and redirect."""
#     conn = get_conn()
#     try:
#         with conn.cursor() as cur:
#             cur.execute("SELECT original_url FROM urls WHERE short_code=%s",(code,))
#             row=cur.fetchone()
#     finally:
#         put_conn(conn)
    
#     if not row:
#         return jsonify({"error": "Not found"}),404
    
#     publish_event({
#         "type": "URL_VISITED",
#         "short_code": code,
#         "ip": request.remote_addr,
#         "user_agent": request.headers.get("User-Agent", ""),
#         "timestamp": datetime.utcnow().isoformat(),
#     })
 
#     return redirect(row[0], code=302)



# @app.route("/api/analytics/<string:code>", methods=["GET"])
# def analytics(code):
#     """GET /api/analytics/<code> — return visit log."""
#     conn = get_conn()
#     try:
#         with conn.cursor() as cur:
#             cur.execute(
#                 "SELECT ip_address, user_agent, visited_at FROM analytics "
#                 "WHERE short_code = %s ORDER BY visited_at DESC",
#                 (code,)
#             )
#             rows = cur.fetchall()
#     finally:
#         put_conn(conn)
 
#     visits = [{"ip": r[0], "user_agent": r[1], "visited_at": str(r[2])} for r in rows]
#     return jsonify({"short_code": code, "visits": visits})
 
 
# # ─── Boot ────────────────────────────────────────────────────────────────────
# if __name__ == "__main__":
#     init_db()
#     connect_rabbit()
#     app.run(host="0.0.0.0", port=5000, debug=False)
# else:
#     # When launched via gunicorn
#     init_db()
#     connect_rabbit()



import os, json, time, threading
from datetime import datetime

import pika
import psycopg2
import psycopg2.pool
from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
from nanoid import generate
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# ─── Config ─────────────────────────────────────────────────────────────────
PG_HOST    = os.getenv("PG_HOST", "postgres")
PG_DB      = os.getenv("PG_DB",   "urlshortener")
PG_USER    = os.getenv("PG_USER", "postgres")
PG_PASS    = os.getenv("PG_PASSWORD", "postgres")
RABBIT_URL = os.getenv("RABBIT_URL", "amqp://guest:guest@rabbitmq:5672")
EXCHANGE   = "url.events"
BASE_URL   = os.getenv("BASE_URL", "http://localhost:5000")

# ─── PostgreSQL connection pool ──────────────────────────────────────────────
def make_pool(retries=10):
    for i in range(retries):
        try:
            pool = psycopg2.pool.ThreadedConnectionPool(
                1, 10,
                host=PG_HOST, dbname=PG_DB,
                user=PG_USER, password=PG_PASS
            )
            print(f"[DB] Connected (pid {os.getpid()})")
            return pool
        except Exception as e:
            print(f"[DB] Attempt {i+1} failed: {e}")
            time.sleep(3)
    raise RuntimeError("Cannot connect to PostgreSQL")

db_pool = make_pool()

def get_conn():
    return db_pool.getconn()

def put_conn(conn):
    db_pool.putconn(conn)

# ─── DB Init — advisory lock prevents concurrent CREATE TABLE races ───────────
# Gunicorn forks N workers; all of them import this module and can race on DDL.
# pg_try_advisory_lock(42) ensures only ONE worker runs the migration at a time.
# IF NOT EXISTS alone is not enough — Postgres can still deadlock on the
# pg_type catalog when two transactions try to register the same type name.
def init_db():
    conn = get_conn()
    try:
        conn.autocommit = True          # advisory lock needs autocommit=True
        with conn.cursor() as cur:
            # Spin until we get the lock (another worker may be running init)
            for _ in range(20):
                cur.execute("SELECT pg_try_advisory_lock(42)")
                if cur.fetchone()[0]:
                    break
                print("[DB] Waiting for advisory lock...")
                time.sleep(0.5)

            # Now run DDL safely — only one worker reaches this point at a time
            cur.execute("""
                CREATE TABLE IF NOT EXISTS urls (
                    id           SERIAL PRIMARY KEY,
                    short_code   VARCHAR(20) UNIQUE NOT NULL,
                    original_url TEXT NOT NULL,
                    created_at   TIMESTAMP DEFAULT NOW()
                );
                CREATE TABLE IF NOT EXISTS analytics (
                    id           SERIAL PRIMARY KEY,
                    short_code   VARCHAR(20) NOT NULL,
                    ip_address   VARCHAR(50),
                    user_agent   TEXT,
                    visited_at   TIMESTAMP DEFAULT NOW()
                );
            """)
            cur.execute("SELECT pg_advisory_unlock(42)")
        print(f"[DB] Tables ready (pid {os.getpid()})")
    finally:
        conn.autocommit = False
        put_conn(conn)

# ─── RabbitMQ Publisher — one connection per worker process ──────────────────
# Each gunicorn worker is a separate OS process; they cannot share a pika
# BlockingConnection. Each worker gets its own connection after fork.
rabbit_channel = None
rabbit_lock    = threading.Lock()

def connect_rabbit(retries=10):
    global rabbit_channel
    for i in range(retries):
        try:
            params     = pika.URLParameters(RABBIT_URL)
            connection = pika.BlockingConnection(params)
            ch         = connection.channel()
            ch.exchange_declare(exchange=EXCHANGE, exchange_type="fanout", durable=True)
            rabbit_channel = ch
            print(f"[RabbitMQ] Connected (pid {os.getpid()})")
            return
        except Exception as e:
            print(f"[RabbitMQ] Attempt {i+1} failed: {e}")
            time.sleep(3)
    print("[RabbitMQ] WARNING: Could not connect — events will be skipped")

def publish_event(payload: dict):
    global rabbit_channel
    with rabbit_lock:
        try:
            if rabbit_channel:
                rabbit_channel.basic_publish(
                    exchange=EXCHANGE,
                    routing_key="",
                    body=json.dumps(payload),
                    properties=pika.BasicProperties(delivery_mode=2),
                )
        except Exception as e:
            print(f"[RabbitMQ] Publish failed, reconnecting: {e}")
            rabbit_channel = None
            try:
                connect_rabbit(retries=3)
                if rabbit_channel:
                    rabbit_channel.basic_publish(
                        exchange=EXCHANGE,
                        routing_key="",
                        body=json.dumps(payload),
                        properties=pika.BasicProperties(delivery_mode=2),
                    )
            except Exception as e2:
                print(f"[RabbitMQ] Retry also failed: {e2}")

# ─── Gunicorn post_fork hook — called in each worker after fork ───────────────
# Gunicorn calls this function (if it exists in the app module) automatically.
# This is the correct place to initialise per-process resources.
def post_fork(server, worker):
    """Called by gunicorn in each worker after fork."""
    init_db()
    connect_rabbit()

# ─── Routes ──────────────────────────────────────────────────────────────────

@app.route("/healthz")
def healthz():
    return {"status": "ok"}, 200


@app.route("/short", methods=["POST"])
def shorten():
    """
    POST /short
    Body: { "url": "https://example.com" }
    Returns: { "short_code": "aB3x9K", "short_url": "http://host/aB3x9K" }
    """
    data = request.get_json(silent=True) or {}
    url  = data.get("url")
    if not url:
        return jsonify({"error": "url is required"}), 400

    short_code = generate(size=6)

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO urls (short_code, original_url) VALUES (%s, %s)",
                (short_code, url),
            )
            conn.commit()
    finally:
        put_conn(conn)

    publish_event({
        "type":         "URL_CREATED",
        "short_code":   short_code,
        "original_url": url,
        "ip":           request.remote_addr,
        "user_agent":   request.headers.get("User-Agent", ""),
        "timestamp":    datetime.utcnow().isoformat(),
    })

    return jsonify({"short_code": short_code, "short_url": f"{BASE_URL}/{short_code}"}), 201


@app.route("/<string:code>", methods=["GET"])
def redirect_short(code):
    """GET /<code> — look up and redirect."""
    # Ignore favicon requests
    if code in ("favicon.ico", "healthz"):
        return "", 204

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT original_url FROM urls WHERE short_code = %s", (code,))
            row = cur.fetchone()
    finally:
        put_conn(conn)

    if not row:
        return jsonify({"error": "Not found"}), 404

    publish_event({
        "type":       "URL_VISITED",
        "short_code": code,
        "ip":         request.remote_addr,
        "user_agent": request.headers.get("User-Agent", ""),
        "timestamp":  datetime.utcnow().isoformat(),
    })

    return redirect(row[0], code=302)


@app.route("/api/analytics/<string:code>", methods=["GET"])
def analytics(code):
    """GET /api/analytics/<code> — return visit log."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT ip_address, user_agent, visited_at FROM analytics "
                "WHERE short_code = %s ORDER BY visited_at DESC",
                (code,),
            )
            rows = cur.fetchall()
    finally:
        put_conn(conn)

    visits = [{"ip": r[0], "user_agent": r[1], "visited_at": str(r[2])} for r in rows]
    return jsonify({"short_code": code, "visits": visits})


# ─── Dev server entry point ───────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    connect_rabbit()
    app.run(host="0.0.0.0", port=5000, debug=False)