-- name: insert_quiz(user_id, title)^
-- Create a quiz
INSERT INTO quizzes (user_id, title) VALUES (:user_id, :title) RETURNING *;

-- name: get_quiz_with_questions(user_id, id)
-- Get a quiz and its questions
SELECT
    q.id AS quiz_id,
    q.user_id AS quiz_user_id,
    q.title AS quiz_title,
    q.created_at AS quiz_created_at,
    q.updated_at AS quiz_updated_at,
    qq.id AS quiz_question_id,
    qq.question AS quiz_question_question,
    qq.answer AS quiz_question_answer,
    qq.explanation AS quiz_question_explanation,
    qq.created_at AS quiz_question_created_at,
    qq.updated_at AS quiz_question_updated_at
FROM quizzes q
LEFT JOIN quiz_questions qq ON q.id = qq.quiz_id
WHERE q.user_id = :user_id AND q.id = :id;

-- name: list_quizzes_with_questions_by_user(user_id)
-- List quizzes with questions by user
SELECT
    q.id AS quiz_id,
    q.user_id AS quiz_user_id,
    q.title AS quiz_title,
    q.created_at AS quiz_created_at,
    q.updated_at AS quiz_updated_at,
    qq.id AS quiz_question_id,
    qq.question AS quiz_question_question,
    qq.answer AS quiz_question_answer,
    qq.explanation AS quiz_question_explanation,
    qq.created_at AS quiz_question_created_at,
    qq.updated_at AS quiz_question_updated_at
FROM quizzes q
LEFT JOIN quiz_questions qq ON q.id = qq.quiz_id
WHERE q.user_id = :user_id;

-- name: update_quiz_title(id, title)^
-- Update a quiz title
UPDATE quizzes SET title = :title, updated_at = CURRENT_TIMESTAMP WHERE id = :id RETURNING *;

-- name: delete_quiz(id)^
-- Delete a quiz
DELETE FROM quizzes WHERE id = :id RETURNING *;
