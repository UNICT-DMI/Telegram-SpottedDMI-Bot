"""/cancel command"""
from telegram import Update
from telegram.ext import CallbackContext
from modules.data import PendingPost
from modules.utils import EventInfo
from .constants import STATE


async def cancel_cmd(update: Update, context: CallbackContext) -> int:
    """Handles the /cancel command.
    Exits from the post pipeline and removes the eventual pending post of the user

    Args:
        update: update event
        context: context passed by the handler

    Returns:
        next state of the conversation
    """
    info = EventInfo.from_message(update, context)
    if not info.is_private_chat:  # you can only cancel a post with a private message
        return STATE["end"]
    pending_post = PendingPost.from_user(user_id=info.user_id)
    if pending_post:  # if the user has a pending post in evaluation, delete it
        group_id = pending_post.group_id
        g_message_id = pending_post.g_message_id
        pending_post.delete_post()

        await info.bot.delete_message(chat_id=group_id, message_id=g_message_id)
        await info.bot.send_message(chat_id=info.chat_id, text="Lo spot precedentemente inviato è stato cancellato")
    else:
        await info.bot.send_message(chat_id=info.chat_id, text="Operazione annullata")
    return STATE["end"]
