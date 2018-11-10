CREATE TABLE IF NOT EXISTS 'Spot_list'(
  'chat_id' int(11) NOT NULL,
  'username' varchar(255),
  'message' text NOT NULL,
  'date' datetime
);

CREATE TABLE user_reactions (
message_id int NOT NULL ,
user_id int NOT NULL,
thumbsup int,
thumbsdown int,
PRIMARY KEY (message_id,user_id)
);
