-- Top 10 most recent posts (a typical "feed" query)
SELECT * FROM posts
ORDER BY created_at DESC
LIMIT 10;

-- Pagination: skip the first 10, then take the next 10 (page 2)
SELECT * FROM posts
ORDER BY created_at DESC
LIMIT 10 OFFSET 10;