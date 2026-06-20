SELECT users.username, posts.caption
FROM users
RIGHT JOIN posts ON users.user_id = posts.user_id;