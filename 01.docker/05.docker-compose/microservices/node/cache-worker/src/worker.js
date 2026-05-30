import dotenv from "dotenv";
import amqp from "amqplib";
dotenv.config();
// ─── In-Memory Cache (replaces Redis) ───────────────────────────────────────
// Simple Map: short_code -> original_url
// Also tracks hit count per code.
const cache = new Map(); // { short_code: { url, hits, cachedAt } }

function cacheSet(short_code, original_url) {
  cache.set(short_code, {
    url: original_url,
    hits: 0,
    cachedAt: new Date().toISOString(),
  });
  console.log(`[Cache] SET ${short_code} -> ${original_url}`);
}

function cacheHit(short_code) {
  if (cache.has(short_code)) {
    cache.get(short_code).hits++;
    console.log(
      `[Cache] HIT  ${short_code} | total hits: ${cache.get(short_code).hits}`
    );
  }
}

// ─── RabbitMQ Consumer ───────────────────────────────────────────────────────
const EXCHANGE = "url.events";
const QUEUE = "cache_q";

async function start(retries = 20) {
  for (let repeater = 0; repeater <= retries; repeater++) {
    try {
      const conn = await amqp.connect(
        process.env.RABBIT_URL || "amqp://guest:guest@rabbitmq:5672"
      );
      const ch = await conn.createChannel();

      await ch.assertExchange(EXCHANGE, "fanout", {
        durable: true,
      });
      await ch.assertQueue(QUEUE, { durable: true });
      await ch.bindQueue(QUEUE, EXCHANGE, "");

      console.log(`[CacheWorker] Listening on queue: ${QUEUE}`);

      ch.consume(QUEUE, (msg) => {
        console.log("message is:", msg);
        // console.log(msg);
        if (!msg) return;
        try {
          const event = JSON.parse(msg.content.toString());
          console.log(event);

          if (event.type === "URL_CREATED") {
            cacheSet(event.short_code, event.original_url);
          } else if (event.type === "URL_VISITED") {
            cacheHit(event.short_code);
          }

          ch.ack(msg);
        } catch (err) {
          console.error(
            "[CacheWorker] Failed to process message:",
            err.message
          );
          ch.nack(msg, false, false);
        }
      });

      // Periodically print cache stats
      setInterval(() => {
        console.log(`[Cache] Stats — ${cache.size} entries:`);
        for (const [code, data] of cache.entries()) {
          console.log(`  ${code}: hits=${data.hits} url=${data.url}`);
        }
      }, 30_000);

      return;
    } catch (error) {
      console.error(
        `[CacheWorker] Connect attempt ${repeater + 1} failed:`,
        error.message
      );
      await new Promise((r) => setTimeout(r, 3000));
    }
  }
  process.exit(1);
}

start().catch(console.error);
