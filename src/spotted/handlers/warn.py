"""/warn command"""
from telegram import Update
from telegram.ext import CallbackContext
from spotted.data import User
from spotted.utils import EventInfo


def warn_cmd(update: Update, context: CallbackContext):
    """Handles the /warn command.
    Warn a user by replying to one of his message in the comment group with /warn

    Args:
        update: update event
        context: context passed by the handler
    """
    info = EventInfo.from_message(update, context)
    g_message = update.message.reply_to_message
    if g_message is None:
        info.bot.send_message(
            chat_id=info.chat_id,
            text="Per warnare qualcuno, rispondi al suo commento con /warn",
        )
    user = User(g_message.from_user.id)
    user.warn(context.bot)
    # g.delete_post()
    # info.edit_inline_keyboard(message_id=g_message_id)
    info.bot.send_message(chat_id=info.chat_id, text="L'utente è stato warnato")
