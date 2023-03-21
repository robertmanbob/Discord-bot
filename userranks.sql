-- This table stores the rank of roles for each server
-- It needs to hold the server ID, the role ID, and the rank of the role (an integer)
CREATE TABLE IF NOT EXISTS ranks (
    server_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,
    rank INT NOT NULL,
    PRIMARY KEY (server_id, role_id)
);