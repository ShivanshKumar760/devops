-- How many posts has each user made?
SELECT user_id, COUNT(*) AS total_posts
FROM posts
GROUP BY user_id;

-- How many likes does each post have? (the classic Instagram "like count")
SELECT post_id, COUNT(*) AS like_count
FROM likes
GROUP BY post_id;

-- Filter groups using HAVING (WHERE filters rows BEFORE grouping; HAVING filters AFTER)
SELECT post_id, COUNT(*) AS like_count
FROM likes
GROUP BY post_id
HAVING COUNT(*) > 100;   -- only posts with more than 100 likes