"""Anonym Comment on a post in the comment group"""
from telegram import Update
from telegram.ext import CallbackContext

from spotted.data import Config
from spotted.utils import EventInfo


async def anonymous_comment_msg(update: Update, context: CallbackContext):
    """Handles a new anonym comment on a post in the comment group.
    Deletes the original post and sends a message with the same text, to avoid any abuse.

    Args:
        update: update event
        context: context passed by the handler
    """
    info = EventInfo.from_message(update, context)

    if Config.post_get("replace_anonymous_comments"):
        reply_to_message_id = info.message.reply_to_message.message_id if info.message.reply_to_message else None
        await info.message.copy(chat_id=info.chat_id, reply_to_message_id=reply_to_message_id)
    await info.message.delete()
