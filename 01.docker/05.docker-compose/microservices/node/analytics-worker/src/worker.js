import dotenv from "dotenv";
import amqp from "amqplib";
import { Pool } from "pg";
dotenv.config();
// ─── PostgreSQL Pool ─────────────────────────────────────────────────────────
const db = new Pool({
  host: process.env.PG_HOST || "postgres",
  port: process.env.PG_PORT || 5432,
  database: process.env.PG_DB || "urlshortener",
  user: process.env.PG_USER || "postgres",
  password: process.env.PG_PASSWORD || "postgres",
});

// ─── RabbitMQ Consumer ────────────────────────────────────────────────────────
const EXCHANGE = "url.events";
const QUEUE = "audit_q";

async function logVisit({ short_code, ip, user_agent, timestamp }) {
  await db.query(
    "INSERT INTO analytics (short_code, ip_address, user_agent, visited_at) VALUES ($1, $2, $3, $4)",
    [
      short_code,
      ip || "unknown",
      user_agent || "",
      timestamp || new Date().toISOString(),
    ]
  );
  console.log(`[Analytics] Logged visit: ${short_code} from ${ip}`);
}

async function start(retries = 10) {
  for (let i = 0; i < retries; i++) {
    try {
      const conn = await amqp.connect(
        process.env.RABBIT_URL || "amqp://guest:guest@rabbitmq:5672"
      );
      const ch = await conn.createChannel();

      await ch.assertExchange(EXCHANGE, "fanout", { durable: true });
      await ch.assertQueue(QUEUE, { durable: true });
      await ch.bindQueue(QUEUE, EXCHANGE, "");

      console.log(`[AnalyticsWorker] Listening on queue: ${QUEUE}`);

      ch.consume(QUEUE, async (msg) => {
        if (!msg) return;
        try {
          const event = JSON.parse(msg.content.toString());

          // Log both creation events and visit events
          if (event.type === "URL_VISITED" || event.type === "URL_CREATED") {
            await logVisit(event);
          }

          ch.ack(msg);
        } catch (err) {
          console.error(
            "[AnalyticsWorker] Failed to process message:",
            err.message
          );
          ch.nack(msg, false, false);
        }
      });

      return;
    } catch (err) {
      console.error(
        `[AnalyticsWorker] Connect attempt ${i + 1} failed:`,
        err.message
      );
      await new Promise((r) => setTimeout(r, 3000));
    }
  }
  process.exit(1);
}

start().catch(console.error);
