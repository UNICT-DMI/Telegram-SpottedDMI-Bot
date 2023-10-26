"""Detect Comment on a post in the comment group"""
from telegram import Update
from telegram.ext import CallbackContext
from modules.data import Config
from modules.utils import EventInfo
from modules.data.db_manager import DbManager


def follow_spot_comment(update: Update, context: CallbackContext):
    """Handles a new comment on a post in the comment group.
    Checks if someone is following the post, and sends them an update in case.

    Args:
        update: update event
        context: context passed by the handler
    """
    info = EventInfo.from_message(update, context)

    if info.chat_id == Config.meme_get('channel_group_id'):
        # Get the spot's message_id
        reply_to_message_id = info.message.message_thread_id
        # Get a list of users who are following the spot
        result = DbManager.select_from(
            table_name = "user_follow",
            select = "user_id, private_message_id",
            where = "message_id = %s",
            where_args = (reply_to_message_id, )
        )

        # Send them an update about the new comment
        for user in result:
            info.message.copy(chat_id=user['user_id'], reply_to_message_id=user['private_message_id'])
