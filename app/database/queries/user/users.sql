-- name: get(id)^
-- Get a user by their ID
SELECT * FROM users WHERE id = :id;

-- name: get_by_email(email)^
-- Get a user by their email
SELECT * FROM users WHERE email = :email;

-- name: get_by_phone_number(phone_number)^
-- Get a user by their phone number
SELECT * FROM users WHERE phone_number = :phone_number;

-- name: get_by_email_or_phone_number(email_or_phone_number)^
-- Get a user by their email or phone number
SELECT * FROM users WHERE email = :email_or_phone_number OR phone_number = :email_or_phone_number;

-- name: insert(name, email, phone_number, hashed_password)^
INSERT INTO users (name, email, phone_number, hashed_password)
VALUES (:name, :email, :phone_number, :hashed_password)
RETURNING *;
