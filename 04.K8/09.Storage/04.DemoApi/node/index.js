import express from "express";
import { Pool } from "pg";

const app = express();
const PORT = 3000 || process.env.PORT; //config map
app.use(express.json());

const pool = new Pool({
  host: process.env.DB_HOST || "postgres-service", //config map
  port: parseInt(process.env.DB_PORT || "5432"), //config map
  database: process.env.DB_NAME || "appdb", //secrets
  user: process.env.DB_USER || "postgres", //secrets
  password: process.env.DB_PASSWORD || "postgres", //secrets
});

async function initDB() {
  await pool.query(
    `CREATE TABLE IF NOT EXISTS items(
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            value TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )`
  );

  console.log("DB initialised");
}

// POST /post  — store an item
app.post("/post", async (req, res) => {
  const { name, value } = req.body;
  if (!name) return res.status(400).json({ error: "name is required" });

  const result = await pool.query(
    "INSERT INTO items (name,value) VALUES ($1,$2) RETURNING *",
    [name, value]
  );
  res.status(201).json(result.rows[0]);
});

// GET /fetch  — retrieve all items
app.get("/fetch", async (req, res) => {
  const result = await pool.query(
    "SELECT * FROM items ORDER BY created_at DESC"
  );
  res.json(result.rows);
});

initDB()
  .then(() => {
    app.listen(PORT, () => console.log("Node.js API listening on :3000"));
  })
  .catch((err) => {
    console.error("DB init failed", err);
    process.exit(1);
  });
