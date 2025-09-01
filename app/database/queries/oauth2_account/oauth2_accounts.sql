-- name: get_by_provider_account(provider, account_id)^
-- Get an OAuth2 account by provider and said provider's account ID
SELECT
    oa.provider AS oauth2_provider,
    oa.account_id AS oauth2_account_id,
    oa.account_email AS oauth2_account_email,
    oa.access_token AS oauth2_access_token,
    oa.refresh_token AS oauth2_refresh_token,
    oa.expires_at AS oauth2_expires_at,
    u.id AS user_id,
    u.name AS user_name,
    u.email AS user_email,
    u.phone_number AS user_phone_number,
    u.created_at AS user_created_at,
    u.updated_at AS user_updated_at
FROM oauth2_accounts oa
JOIN users u ON oa.user_id = u.id
WHERE provider = :provider AND account_id = :account_id;

-- name: insert(user_id, provider, account_id, account_email, access_token, refresh_token, expires_at)!
-- Insert an OAuth2 account for the given user and provider. If the given user and provider pair already exists,
-- replaces the existing account with the new one.
INSERT INTO oauth2_accounts (user_id, provider, account_id, account_email, access_token, refresh_token, expires_at)
VALUES (:user_id, :provider, :account_id, :account_email, :access_token, :refresh_token, :expires_at)
ON CONFLICT (user_id, provider) DO UPDATE SET
    account_id = excluded.account_id,
    account_email = excluded.account_email,
    access_token = excluded.access_token,
    refresh_token = excluded.refresh_token,
    expires_at = excluded.expires_at;
