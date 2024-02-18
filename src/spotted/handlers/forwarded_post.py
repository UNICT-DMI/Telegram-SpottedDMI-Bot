"""Message forwarded by the telegram channel"""

from telegram import Update
from telegram.ext import CallbackContext

from spotted.utils import EventInfo


async def forwarded_post_msg(update: Update, context: CallbackContext):
    """Handles the post forwarded in the channel group.
    Sends a reply in the channel group and stores it in the database, so that the post can be voted

    Args:
        update: update event
        context: context passed by the handler
    """
    info = EventInfo.from_message(update, context)
    if info.message is None or not info.is_forwarded_post:
        return

    await info.send_post_to_channel_group()
