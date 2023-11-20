"""Detect Comment on a post in the comment group"""
from telegram import Update
from telegram.ext import CallbackContext

from spotted.data import User
from spotted.utils import EventInfo


async def follow_spot_comment(update: Update, context: CallbackContext):
    """Handles a new comment on a post in the comment group.
    Checks if someone is following the post, and sends them an update in case.

    Args:
        update: update event
        context: context passed by the handler
    """
    info = EventInfo.from_message(update, context)

    # Get the spot's message_id
    reply_to_message_id = info.message.message_thread_id
    # Get a list of users who are following the spot
    users = User.following_users(reply_to_message_id)

    # Send them an update about the new comment
    for user in users:
        # Avoid sending if it's made by the same user
        if not user.user_id == info.message.from_user.id:
            await info.message.copy(chat_id=user.user_id, reply_to_message_id=user.private_message_id)
