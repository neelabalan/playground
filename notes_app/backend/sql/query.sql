-- name: GetUser :one
SELECT * FROM users
WHERE id = ? LIMIT 1;

-- name: GetUserByEmail :one
SELECT * from users
WHERE email = ? LIMIT 1;

-- name: ListUsers :many
SELECT * FROM users
ORDER BY username;

-- name: CreateUser :one
INSERT INTO users (
  username, email, password, refresh_token
) VALUES (
  ?, ?, ?, ?
)
RETURNING *;

-- name: GetUserWithRefreshToken :one
SELECT * FROM users
WHERE refresh_token = ?;

-- name: UpdateRefreshToken :one
UPDATE users
SET refresh_token = ?
where email = ?
RETURNING *;

-- name: UpdateUser :exec
UPDATE users
SET username = ?,
email = ?,
password = ?
WHERE id = ?;

-- name: DeleteUser :exec
DELETE FROM users
WHERE id = ?;

-- name: GetNote :one
SELECT * FROM notes n
WHERE n.user_id=(SELECT u.id FROM users u WHERE u.email=?)
AND n.id=?;

-- name: ListNotes :many
SELECT * FROM notes n
WHERE n.user_id=(SELECT u.id FROM users u WHERE u.email=?)
ORDER BY created_at
LIMIT ? OFFSET ?;


-- name: CreateNote :one
INSERT INTO notes (user_id, note, tags, created_at, updated_at)
VALUES (
    (SELECT u.id FROM users u WHERE u.email = ?),
    ?, ?, ?, ?
)
RETURNING id, user_id, note, tags, created_at, updated_at;


-- name: UpdateNote :exec
UPDATE notes
SET note = ?,
tags = ?,
updated_at = ?
WHERE id = ? AND user_id = ?;

-- name: DeleteNote :exec
DELETE FROM notes
WHERE id = ? AND user_id = ?;
