-- Add up migration script here
CREATE TABLE oauth2_accounts(
    user_id INTEGER NOT NULL,
    provider TEXT NOT NULL,
    account_id TEXT NOT NULL,
    account_email TEXT,
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    expires_at DATETIME,
    PRIMARY KEY(user_id, provider),
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);
