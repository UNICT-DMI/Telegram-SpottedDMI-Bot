"""/ban command"""
from telegram import Update
from telegram.ext import CallbackContext

from spotted.data import PendingPost, User
from spotted.utils import EventInfo


async def ban_cmd(update: Update, context: CallbackContext):
    """Handles the /ban command.
    Ban a user by replying to one of his pending posts with /ban

    Args:
        update: update event
        context: context passed by the handler
    """
    info = EventInfo.from_message(update, context)
    g_message_id = update.message.reply_to_message.message_id
    pending_post = PendingPost.from_group(admin_group_id=info.chat_id, g_message_id=g_message_id)

    if pending_post is None:
        await info.bot.send_message(chat_id=info.chat_id, text="Per bannare qualcuno, rispondi al suo post con /ban")
        return

    user = User(pending_post.user_id)
    user.ban()
    pending_post.delete_post()
    await info.edit_inline_keyboard(message_id=g_message_id)
    await info.bot.send_message(chat_id=info.chat_id, text="L'utente è stato bannato")
