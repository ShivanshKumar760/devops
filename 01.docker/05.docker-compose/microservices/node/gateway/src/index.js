import express from "express";
import { Pool } from "pg";
import amqp from "amqplib";
import cors from "cors";
import dotenv from "dotenv";
import { nanoid } from "nanoid";
dotenv.config();
const app = express();
app.use(cors());
app.use(express.urlencoded({ extended: true }));
app.use(express.json());

// ─── PostgreSQL Pool ────────────────────────────────────────────────────────
const db = new Pool({
  host: process.env.PG_HOST || "postgres",
  port: process.env.PG_PORT || 5432,
  database: process.env.PG_DB || "urlshortener",
  user: process.env.PG_USER || "postgres",
  password: process.env.PG_PASSWORD || "postgres",
});

let rabbitChannel = null;
const EXCHANGE = "url.events";

async function connectRabbit(retries = 20) {
  for (let i = 0; i <= 20; i++) {
    try {
      const conn = await amqp.connect(
        process.env.RABBIT_URL || "amqp://guest:guest@rabbitmq:5672"
      );
      rabbitChannel = await conn.createChannel();
      await rabbitChannel.assertExchange(EXCHANGE, "fanout", {
        durable: true,
      });
      console.log("[RabbitMQ] Connected and exchange ready");
      return;
    } catch (error) {
      console.error(
        `[RabbitMQ] Connection attempt ${i + 1} failed:`,
        err.message
      );
      await new Promise((r) => setTimeout(r, 3000));
    }
  }
  throw new Error("Could not connect to RabbitMQ after retries");
}

// ─── DB Init ────────────────────────────────────────────────────────────────
async function initDB() {
  await db.query(`
    CREATE TABLE IF NOT EXISTS urls (
      id          SERIAL PRIMARY KEY,
      short_code  VARCHAR(20) UNIQUE NOT NULL,
      original_url TEXT NOT NULL,
      created_at  TIMESTAMP DEFAULT NOW()
    );
    CREATE TABLE IF NOT EXISTS analytics (
      id          SERIAL PRIMARY KEY,
      short_code  VARCHAR(20) NOT NULL,
      ip_address  VARCHAR(50),
      user_agent  TEXT,
      visited_at  TIMESTAMP DEFAULT NOW()
    );
  `);
  console.log("[DB] Tables ready");
}

app.post("/short", async (req, res) => {
  const { url } = req.body;
  if (!url) return res.status(400).json({ error: "url is required" });

  const short_code = nanoid(6);

  await db.query("INSERT INTO urls (short_code,original_url) VALUES ($1,$2)", [
    short_code,
    url,
  ]);

  if (rabbitChannel) {
    const payload = JSON.stringify({
      type: "URL_CREATED",
      short_code,
      original_url: url,
      ip: req.ip,
      user_agent: req.headers["user-agent"] || "",
      timestamp: new Date().toISOString(),
    });
    rabbitChannel.publish(EXCHANGE, "", Buffer.from(payload));
  }
  return res.status(201).json({
    short_code,
    short_url: `${
      process.env.BASE_URL || "http://localhost:3000"
    }/${short_code}`,
  });
});

// GET /:code — redirect
app.get("/:code", async (req, res) => {
  const { code } = req.params;
  const result = await db.query(
    "SELECT original_url FROM urls WHERE short_code = $1",
    [code]
  );
  if (result.rows.length === 0)
    return res.status(404).json({ error: "Not found" });

  // Broadcast visit event
  if (rabbitChannel) {
    const payload = JSON.stringify({
      type: "URL_VISITED",
      short_code: code,
      ip: req.ip,
      user_agent: req.headers["user-agent"] || "",
      timestamp: new Date().toISOString(),
    });
    rabbitChannel.publish(EXCHANGE, "", Buffer.from(payload));
  }

  return res.redirect(302, result.rows[0].original_url);
});

// GET /api/analytics/:code
app.get("/api/analytics/:code", async (req, res) => {
  const result = await db.query(
    "SELECT ip_address, user_agent, visited_at FROM analytics WHERE short_code = $1 ORDER BY visited_at DESC",
    [req.params.code]
  );
  res.json({ short_code: req.params.code, visits: result.rows });
});

// ─── Boot ───────────────────────────────────────────────────────────────────
async function start() {
  await initDB();
  await connectRabbit();
  const PORT = process.env.PORT || 3000;
  app.listen(PORT, () => console.log(`[Gateway] Listening on port ${PORT}`));
}

start().catch(console.error);
