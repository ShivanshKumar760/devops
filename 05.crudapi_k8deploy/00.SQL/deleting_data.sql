-- Delete one specific like (a user "unlikes" a post)
DELETE FROM likes
WHERE user_id = 2 AND post_id = 2;

-- Delete all posts by a deleted user
DELETE FROM posts WHERE user_id = 1;