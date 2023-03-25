-- This table stores of the configuration of the welcome cog for each server.
-- It will need server ID, whether or not welcome is enabled and the channel ID.
-- Default to disabled and channel ID 0.
CREATE TABLE IF NOT EXISTS welcome (
    server_id BIGINT NOT NULL,
    wenabled BOOLEAN NOT NULL DEFAULT FALSE,
    channel_id BIGINT NOT NULL DEFAULT 0,
    PRIMARY KEY (server_id)
);