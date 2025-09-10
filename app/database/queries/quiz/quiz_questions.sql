-- name: insert_quiz_question(quiz_id, question, answer, explanation)^
INSERT INTO quiz_questions (quiz_id, question, answer, explanation)
VALUES (:quiz_id, :question, :answer, :explanation)
RETURNING *;

-- name: list_questions_in_quiz(quiz_id)
SELECT * FROM quiz_questions WHERE quiz_id = :quiz_id;

-- name: delete_quiz_question(quiz_id, id)^
DELETE FROM quiz_questions WHERE quiz_id = :quiz_id AND id = :id RETURNING *;
