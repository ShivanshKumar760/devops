-- A user updates their bio
UPDATE users
SET bio = 'Building rockets 🚀 and memes'
WHERE user_id = 1;

-- Update multiple columns at once
UPDATE users
SET full_name = 'Elon R. Musk', bio = 'CEO'
WHERE username = 'elonmusk';