-- Classify posts by how many likes they have
SELECT
    posts.post_id,
    COUNT(likes.user_id) AS like_count,
    CASE
        WHEN COUNT(likes.user_id) = 0 THEN 'No likes'
        WHEN COUNT(likes.user_id) < 10 THEN 'Low engagement'
        WHEN COUNT(likes.user_id) < 100 THEN 'Decent engagement'
        ELSE 'Viral 🔥'
    END AS engagement_level
FROM posts
LEFT JOIN likes ON posts.post_id = likes.post_id
GROUP BY posts.post_id;