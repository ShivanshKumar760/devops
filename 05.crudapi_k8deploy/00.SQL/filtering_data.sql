-- All posts by a specific user
SELECT * FROM posts WHERE user_id = 1;

-- Posts after a certain date
SELECT * FROM posts WHERE created_at > '2026-01-01';

-- Combine conditions
SELECT * FROM posts
WHERE user_id = 1 AND created_at > '2026-01-01';

-- Match against a list
SELECT * FROM users WHERE user_id IN (1, 2, 3);

-- Range
SELECT * FROM posts WHERE post_id BETWEEN 10 AND 20;

-- NULL checks (never use = for NULL)
SELECT * FROM users WHERE bio IS NULL;