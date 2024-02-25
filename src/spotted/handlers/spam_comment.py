"""Anonym Comment on a post in the comment group"""

from telegram import Update
from telegram.ext import CallbackContext

from spotted.data import Config
from spotted.utils import EventInfo


async def spam_comment_msg(update: Update, context: CallbackContext) -> None:
    """Handles a spam comment on a post in the comment group.
    Deletes the original post.

    Args:
        update: update event
        context: context passed by the handler
    """
    info = EventInfo.from_message(update, context)
    for message in Config.post_get("blacklist_messages"):
        if message in info.message.text:
            await info.message.delete()
            return
