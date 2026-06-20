INSERT INTO users (username, email, full_name)
VALUES ('elonmusk', 'elon@example.com', 'Elon Musk');

-- Insert a post from that user (user_id = 1, assuming first row)
INSERT INTO posts (user_id, caption, image_url)
VALUES (1, 'Beautiful sunset 🌅', 'https://cdn.example.com/img1.jpg');

-- Insert multiple rows at once
INSERT INTO users (username, email, full_name) VALUES
    ('priya_d', 'priya@example.com', 'Priya Desai'),
    ('rahul99', 'rahul@example.com', 'Rahul Sharma');

-- Insert Likes for different users
INSERT INTO likes (user_id , post_id) VALUES
    (1, 1),  -- Elon likes his own post
    (2, 1),  -- Priya likes Elon's post
    (3, 1);  -- Rahul likes Elon's post


INSERT INTO posts (user_id, caption, image_url)
VALUES (2, 'Beautiful Evening 🌅', 'https://cdn.example.com/img1.jpg');
INSERT INTO posts (user_id, caption, image_url)
VALUES (3, 'Beautiful Night 🌑', 'https://cdn.example.com/img1.jpg');
INSERT INTO posts (user_id, caption, image_url)
VALUES (1, 'Amazing Night in goa 🌑', 'https://cdn.example.com/img1.jpg');

INSERT INTO likes (user_id , post_id) VALUES
    (1, 2),  -- Elon likes his own post
    (2, 2),  -- Priya likes Elon's post
    (3, 2);  -- Rahul likes Elon's post
    
INSERT INTO likes (user_id , post_id) VALUES
    (1, 3),  -- Elon likes his own post
    (2, 3),  -- Priya likes Elon's post
    (3, 3);  -- Rahul likes Elon's post