.. _dbschema:

Database schema
===========================================
This is the schema of the database used to store information about the spots and their reactions

.. mermaid::

   erDiagram
   "admin_votes" {
      admin_id BIGINT PK
      g_message_id BIGINT PK
      admin_group_id BIGINT PK
      is_upvote BOOLEAN
      credit_username VARCHAR
      message_date TIMESTAMP
   }

   "published_post" {
      channel_id BIGINT PK
      c_message_id BIGINT PK
      message_date TIMESTAMP
   }

   "spot_report" {
      user_id BIGINT PK
      channel_id BIGINT
      c_message_id BIGINT PK
      g_message_id BIGINT
      admin_group_id BIGINT
      message_date TIMESTAMP
   }

   published_post ||--o{ spot_report : receives

.. mermaid::

   erDiagram
   "credited_users" {
      user_id BIGINT PK
   }

   "banned_users" {
      user_id BIGINT PK
      ban_date TIMESTAMP
   }

.. mermaid::

   erDiagram
   "user_report" {
      user_id BIGINT PK
      target_username VARCHAR(32) PK
      g_message_id BIGINT
      admin_group_id BIGINT
      message_date TIMESTAMP PK
   }

   "user_follow" {
      user_id BIGINT PK
      message_id BIGINT PK
      private_message_id BIGINT
      follow_date TIMESTAMP
   }

