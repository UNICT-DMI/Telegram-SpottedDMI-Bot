"""/ban command"""
from telegram import Update
from telegram.ext import CallbackContext
from modules.data import config_map, PendingPost, User
from modules.utils import EventInfo


def ban_cmd(update: Update, context: CallbackContext):
    """Handles the /ban command.
    Ban a user by replying to one of his pending posts with /ban

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler
    """
    info = EventInfo.from_message(update, context)
    if info.chat_id == config_map['meme']['group_id']:  # you have to be in the admin group
        g_message_id = update.message.reply_to_message.message_id
        pending_post = PendingPost.from_group(group_id=info.chat_id, g_message_id=g_message_id)

        if pending_post is None:
            info.bot.send_message(chat_id=info.chat_id, text="Per bannare qualcuno, rispondi al suo post con /ban")
            return

        user = User(pending_post.user_id)
        user.ban()
        pending_post.delete_post()
        info.edit_inline_keyboard(message_id=g_message_id)
        info.bot.send_message(chat_id=info.chat_id, text="L'utente è stato bannato")
