"""Anonym Comment on a post in the comment group"""
from telegram import Update
from telegram.ext import CallbackContext
from modules.data import config_map
from modules.utils import EventInfo


def anonymous_comment_msg(update: Update, context: CallbackContext):
    """Handles a new anonym comment on a post in the comment group.
    Deletes the original post and sends a message with the same text, to avoid any abuse.

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler
    """
    info = EventInfo.from_message(update, context)

    if info.chat_id == config_map['meme']['channel_group_id'] and info.message.via_bot is None:
        if config_map['meme']['replace_anonymous_comments']:
            reply_to_message_id = info.message.reply_to_message.message_id if info.message.reply_to_message else None
            info.message.copy(chat_id=info.chat_id, reply_to_message_id=reply_to_message_id)
        info.message.delete()
