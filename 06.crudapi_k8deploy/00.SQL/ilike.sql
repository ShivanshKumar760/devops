
UPDATE users SET username = 'PRIYA_D' WHERE username = 'priya_d';
-- Find users whose username contains "priya", regardless of case
SELECT * FROM users WHERE username LIKE '%priya%'; --this will check the case-sensitive match

SELECT * FROM users WHERE username LIKE '%priya%'; -- this wont check the case sensitive match 

-- Starts with "el"
SELECT * FROM users WHERE username ILIKE 'el%';

-- Ends with "99"
SELECT * FROM users WHERE username ILIKE '%99';