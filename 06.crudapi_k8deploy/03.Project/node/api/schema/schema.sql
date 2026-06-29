-- schema.sql — identical to the Python version
CREATE TABLE users (
    user_id      SERIAL PRIMARY KEY,
    username     VARCHAR(50) UNIQUE NOT NULL,
    email        VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    bio          TEXT,
    created_at   TIMESTAMP DEFAULT NOW()
);

CREATE TABLE posts (
    post_id      SERIAL PRIMARY KEY,
    user_id      INTEGER NOT NULL REFERENCES users(user_id),
    caption      TEXT,
    image_url    VARCHAR(255) NOT NULL,
    created_at   TIMESTAMP DEFAULT NOW()
);

CREATE TABLE likes (
    user_id      INTEGER NOT NULL REFERENCES users(user_id),
    post_id      INTEGER NOT NULL REFERENCES posts(post_id),
    liked_at     TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, post_id)
);