CREATE TABLE IF NOT EXISTS 'Spot_list'(
message_id NOT NULL,
chat_id int NOT NULL,
published int,
PRIMARY KEY (message_id,user_id)
  
);

CREATE TABLE user_reactions (
message_id int NOT NULL ,
user_id int NOT NULL,
thumbsup int,
thumbsdown int,
PRIMARY KEY (message_id,user_id)
);
