"""
Cache Worker (Python)
Subscribes to cache_q on the url.events fanout exchange.
Uses a plain Python dict as in-memory cache (replaces Redis).
"""

import os, json, time
import pika
from dotenv import load_dotenv

load_dotenv()

RABBIT_URL = os.getenv("RABBIT_URL", "amqp://guest:guest@rabbitmq:5672")
EXCHANGE   = "url.events"
QUEUE      = "cache_q"

# ─── In-Memory Cache ─────────────────────────────────────────────────────────
cache: dict[str, dict] = {}   # { short_code: { url, hits, cached_at } }

def cache_set(short_code: str, original_url: str):
    cache[short_code] = {"url": original_url, "hits": 0, "cached_at": time.time()}
    print(f"[Cache] SET  {short_code} -> {original_url}")

def cache_hit(short_code: str):
    if short_code in cache:
        cache[short_code]["hits"] += 1
        print(f"[Cache] HIT  {short_code} | total hits: {cache[short_code]['hits']}")

# ─── Message Handler ─────────────────────────────────────────────────────────
def on_message(ch, method, _props, body):
    try:
        event = json.loads(body)
        if event.get("type") == "URL_CREATED":
            cache_set(event["short_code"], event["original_url"])
        elif event.get("type") == "URL_VISITED":
            cache_hit(event["short_code"])
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"[CacheWorker] Error: {e}")
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

            print(f"[CacheWorker] Listening on queue: {QUEUE}")
            ch.start_consuming()
            return
        except Exception as e:
            print(f"[CacheWorker] Attempt {i+1} failed: {e}")
            time.sleep(3)

if __name__ == "__main__":
    start()