-- Add up migration script here
CREATE TABLE users(
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT,
    phone_number TEXT,
    hashed_password TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK(email IS NOT NULL OR phone_number IS NOT NULL)
);
