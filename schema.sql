-- Store a table of users with their associated Discord IDs, last seen,
-- last message, and last Discord username.
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    last_seen DATETIME,
    last_message TEXT,
    last_username TEXT
);
