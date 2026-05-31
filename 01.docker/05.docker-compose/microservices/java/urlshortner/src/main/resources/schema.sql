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