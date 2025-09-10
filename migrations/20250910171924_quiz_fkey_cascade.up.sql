-- Add up migration script here
CREATE TABLE _temp_quizzes(
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    title TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE _temp_quiz_questions(
    id INTEGER PRIMARY KEY,
    quiz_id INTEGER NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    explanation TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE ON UPDATE CASCADE
);

INSERT INTO _temp_quizzes SELECT * FROM quizzes;
INSERT INTO _temp_quiz_questions SELECT * FROM quiz_questions;

DROP TABLE quizzes;
DROP TABLE quiz_questions;

ALTER TABLE _temp_quizzes RENAME TO quizzes;
ALTER TABLE _temp_quiz_questions RENAME TO quiz_questions;
