CREATE TABLE IF NOT EXISTS pending_spot (
	message_id NOT NULL,
	user_id int NOT NULL,
	published int,
	PRIMARY KEY (message_id, user_id)
);

CREATE TABLE IF NOT EXISTS user_reactions (
	message_id int NOT NULL,
	user_id int NOT NULL,
	thumbsup int,
	thumbsdown int,
	PRIMARY KEY (message_id, user_id)
);
