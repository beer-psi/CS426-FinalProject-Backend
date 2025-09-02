-- name: get(token)^
-- Checks if a JWT token is in the denylist.
SELECT * FROM token_denylist WHERE token = :token;

-- name: insert(token, expires_at)!
-- Adds a token to the denylist.
INSERT INTO token_denylist (token, expires_at) VALUES (:token, :expires_at);

-- name: delete(token)!
-- Removes a token from the denylist.
DELETE FROM token_denylist WHERE token = :token;
