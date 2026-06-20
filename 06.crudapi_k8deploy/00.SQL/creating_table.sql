-- USERS table: one row per Instagram user
CREATE TABLE users (
    user_id     SERIAL PRIMARY KEY,             -- PK: uniquely identifies each user
    username    VARCHAR(50) UNIQUE NOT NULL,
    email       VARCHAR(100) UNIQUE NOT NULL,
    full_name   VARCHAR(100),
    bio         TEXT,
    created_at  TIMESTAMP DEFAULT NOW()
);




-- POSTS table: one row per post, each post belongs to exactly one user
CREATE TABLE posts (
    post_id     SERIAL PRIMARY KEY,              -- PK: uniquely identifies each post
    user_id     INTEGER NOT NULL REFERENCES users(user_id), -- FK: links post -> owner
    caption     TEXT,
    image_url   VARCHAR(255),
    created_at  TIMESTAMP DEFAULT NOW()
);


-- LIKES table: a JUNCTION TABLE connecting users and posts (many-to-many)
CREATE TABLE likes (
    user_id     INTEGER NOT NULL REFERENCES users(user_id), -- FK -> users
    post_id     INTEGER NOT NULL REFERENCES posts(post_id), -- FK -> posts
    liked_at    TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, post_id)  -- COMPOSITE KEY: a user can like a post only once
);