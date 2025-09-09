-- Add up migration script here
ALTER TABLE conversations ADD COLUMN require_member_approval BOOLEAN DEFAULT FALSE;

-- Note that we do not add a strict foreign key requirement here since we want to
-- keep the trail even when said user has deleted their account
ALTER TABLE conversation_participants ADD COLUMN added_by_user_id INTEGER NOT NULL;

CREATE TABLE conversation_participants_pending_approval (
    conversation_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    added_by_user_id INTEGER NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (conversation_id, user_id),
    FOREIGN KEY (conversation_id) REFERENCES conversations(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
    -- no fkey constraint for added_by_user_id for the same reasons
);
