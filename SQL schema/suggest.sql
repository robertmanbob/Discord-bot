-- This table stores the configuration of suggest.py for each server
-- It needs to hold the server ID, a boolean for whether or not suggestions are enabled that defaults to false, and the channel ID for the suggestions channel
CREATE TABLE IF NOT EXISTS suggest (
    server_id BIGINT NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT FALSE,
    channel_id BIGINT NOT NULL DEFAULT 0,
    PRIMARY KEY (server_id)
);

-- Add event_id column to suggest table
ALTER TABLE suggest ADD COLUMN event_id BIGINT NOT NULL DEFAULT 0;