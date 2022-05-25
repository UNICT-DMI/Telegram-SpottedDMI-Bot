"""Message forwarded by the telegram channel"""
from telegram import Update
from telegram.ext import CallbackContext
from modules.data import Config
from modules.utils import EventInfo


def forwarded_post_msg(update: Update, context: CallbackContext):
    """Handles the post forwarded in the channel group.
    Sends a reply in the channel group and stores it in the database, so that the post can be voted

    Args:
        update: update event
        context: context passed by the handler
    """
    info = EventInfo.from_message(update, context)
    if update.message is None or update.message.forward_from_chat is None:
        return

    if info.chat_id == Config.meme_get('channel_group_id')\
        and info.forward_from_chat_id == Config.meme_get('channel_id'):
        info.send_post_to_channel_group()
