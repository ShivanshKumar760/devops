SELECT posts.caption, users.username
FROM posts
INNER JOIN users ON posts.user_id = users.user_id;