/*Used to instantiate the database the first time*/
CREATE TABLE IF NOT EXISTS pending_meme
(
  user_id BIGINT NOT NULL,
  u_message_id BIGINT NOT NULL,
  g_message_id BIGINT NOT NULL,
  group_id BIGINT NOT NULL,
  message_date TIMESTAMP,
  PRIMARY KEY (group_id, g_message_id)
);
-----
CREATE TABLE IF NOT EXISTS published_meme
(
  channel_id BIGINT NOT NULL,
  c_message_id BIGINT NOT NULL,
  PRIMARY KEY (channel_id, c_message_id)
);
-----
CREATE TABLE IF NOT EXISTS votes
(
  user_id BIGINT NOT NULL,
  c_message_id BIGINT NOT NULL,
  channel_id BIGINT NOT NULL,
  vote varchar(4) NOT NULL,
  PRIMARY KEY (user_id, c_message_id, channel_id),
  FOREIGN KEY (c_message_id, channel_id) REFERENCES published_meme (c_message_id, channel_id) ON DELETE CASCADE ON UPDATE CASCADE
);
-----
CREATE TABLE IF NOT EXISTS admin_votes
(
  admin_id BIGINT NOT NULL,
  g_message_id BIGINT NOT NULL,
  group_id BIGINT NOT NULL,
  is_upvote boolean NOT NULL,
  PRIMARY KEY (admin_id, g_message_id, group_id),
  FOREIGN KEY (g_message_id, group_id) REFERENCES pending_meme (g_message_id, group_id) ON DELETE CASCADE ON UPDATE CASCADE
);
-----
CREATE TABLE IF NOT EXISTS credited_users
(
  user_id BIGINT NOT NULL,
  PRIMARY KEY (user_id)
);
-----
CREATE TABLE IF NOT EXISTS banned_users
(
  user_id BIGINT NOT NULL,
  PRIMARY KEY (user_id)
);
-----
CREATE TABLE IF NOT EXISTS spot_report
(
  user_id BIGINT NOT NULL,
  channel_id BIGINT NOT NULL,
  c_message_id BIGINT NOT NULL,
  g_message_id BIGINT NOT NULL,
  group_id BIGINT NOT NULL,
  PRIMARY KEY (user_id, c_message_id),
  FOREIGN KEY (c_message_id) REFERENCES published_meme (c_message_id) ON DELETE CASCADE ON UPDATE CASCADE
);
-----
CREATE TABLE IF NOT EXISTS user_report
(
  user_id BIGINT NOT NULL,
  target_username VARCHAR(32) NOT NULL,
  g_message_id BIGINT NOT NULL,
  group_id BIGINT NOT NULL,
  message_date TIMESTAMP NOT NULL,
  PRIMARY KEY (user_id, target_username, message_date)
);
