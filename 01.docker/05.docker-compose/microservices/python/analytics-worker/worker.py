"""
Analytics Worker (Python)
Subscribes to audit_q on the url.events fanout exchange.
Appends visit records to the analytics table in PostgreSQL.
"""

import os, json, time
import pika
import psycopg2
from dotenv import load_dotenv

load_dotenv()

RABBIT_URL = os.getenv("RABBIT_URL", "amqp://guest:guest@rabbitmq:5672")
PG_HOST    = os.getenv("PG_HOST", "postgres")
PG_DB      = os.getenv("PG_DB",   "urlshortener")
PG_USER    = os.getenv("PG_USER", "postgres")
PG_PASS    = os.getenv("PG_PASSWORD", "postgres")
EXCHANGE   = "url.events"
QUEUE      = "audit_q"

# ─── DB helper ───────────────────────────────────────────────────────────────
def get_db(retries=10):
    for i in range(retries):
        try:
            conn = psycopg2.connect(
                host=PG_HOST, dbname=PG_DB, user=PG_USER, password=PG_PASS
            )
            print("[AnalyticsWorker] DB connected")
            return conn
        except Exception as e:
            print(f"[AnalyticsWorker] DB attempt {i+1} failed: {e}")
            time.sleep(3)
    raise RuntimeError("Cannot connect to DB")

db_conn = get_db()

def log_visit(event: dict):
    global db_conn
    try:
        with db_conn.cursor() as cur:
            cur.execute(
                "INSERT INTO analytics (short_code, ip_address, user_agent, visited_at) "
                "VALUES (%s, %s, %s, %s)",
                (
                    event.get("short_code"),
                    event.get("ip", "unknown"),
                    event.get("user_agent", ""),
                    event.get("timestamp"),
                )
            )
            db_conn.commit()
        print(f"[Analytics] Logged: {event.get('short_code')} from {event.get('ip')}")
    except Exception as e:
        db_conn.rollback()
        print(f"[Analytics] DB error: {e}")

# ─── Message Handler ─────────────────────────────────────────────────────────
def on_message(ch, method, _props, body):
    try:
        event = json.loads(body)
        if event.get("type") in ("URL_CREATED", "URL_VISITED"):
            log_visit(event)
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"[AnalyticsWorker] Error: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

# ─── Boot ────────────────────────────────────────────────────────────────────
def start(retries=10):
    for i in range(retries):
        try:
            params = pika.URLParameters(RABBIT_URL)
            connection = pika.BlockingConnection(params)
            ch = connection.channel()

            ch.exchange_declare(exchange=EXCHANGE, exchange_type="fanout", durable=True)
            ch.queue_declare(queue=QUEUE, durable=True)
            ch.queue_bind(queue=QUEUE, exchange=EXCHANGE)
            ch.basic_consume(queue=QUEUE, on_message_callback=on_message)

            print(f"[AnalyticsWorker] Listening on queue: {QUEUE}")
            ch.start_consuming()
            return
        except Exception as e:
            print(f"[AnalyticsWorker] Attempt {i+1} failed: {e}")
            time.sleep(3)

if __name__ == "__main__":
    start()