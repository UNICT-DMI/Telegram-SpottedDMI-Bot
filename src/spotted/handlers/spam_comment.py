"""Anonym Comment on a post in the comment group"""

from telegram import Update
from telegram.ext import CallbackContext

from spotted.data import Config
from spotted.utils import EventInfo


async def spam_comment_msg(update: Update, context: CallbackContext) -> None:
    """Handles a spam comment on a post in the comment group.
    Deletes the original post and bans the user.

    Args:
        update: update event
        context: context passed by the handler
    """
    info = EventInfo.from_message(update, context)
    # The following code performs a safety check.
    # The filter already ensures that the message's text contains the spam word
    for message in Config.post_get("blacklist_messages"):
        if message in info.message.text:
            await info.message.delete()
            await info.bot.ban_chat_member(
                chat_id=info.chat_id,
                user_id=info.message.from_user.id,
            )
            return
