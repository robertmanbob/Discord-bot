-- Table for holding name replies
-- Needs to hold the following information:
--  -- Server ID
--  -- Name to reply to
--  -- URL of image or gif to reply with

CREATE TABLE namereply (
  user_name VARCHAR(255) NOT NULL,
  reply_url VARCHAR(255) NOT NULL,
  PRIMARY KEY (user_name)
);