-- Add up migration script here
CREATE TABLE token_denylist(
    token TEXT PRIMARY KEY,
    expires_at DATETIME NOT NULL
);
