-- This table stores the configuration of roleping.py for each server
-- It needs to hold the server ID, a timer duration, whether or not roleping is enabled, the role ID, and the UNIX timestamp for the next roleping
CREATE TABLE IF NOT EXISTS roleping (
    server_id BIGINT NOT NULL,
    timer_duration INT NOT NULL,
    rpenabled BOOLEAN NOT NULL,
    role_id BIGINT NOT NULL,
    next_roleping BIGINT NOT NULL,
    PRIMARY KEY (server_id)
);

-- Add a min_rank column to the roleping table
ALTER TABLE roleping ADD COLUMN min_rank INT NOT NULL DEFAULT 0;