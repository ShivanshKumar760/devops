-- Newest posts first
SELECT * FROM posts ORDER BY created_at DESC;

-- Oldest first (ASC is the default, so it's optional)
SELECT * FROM posts ORDER BY created_at ASC;

-- Sort by multiple columns: most-liked users, then alphabetically
SELECT user_id, COUNT(*) AS total_posts
FROM posts
GROUP BY user_id
ORDER BY total_posts DESC, user_id DESC; -- so here it sorts by total_posts first, then user_id to break ties

SELECT user_id, COUNT(*) AS total_posts
FROM posts
GROUP BY user_id
ORDER BY total_posts ASC, user_id DESC; 