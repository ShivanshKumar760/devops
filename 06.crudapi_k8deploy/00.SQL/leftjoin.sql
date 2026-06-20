SELECT users.username, posts.caption
FROM users
LEFT JOIN posts ON users.user_id = posts.user_id;