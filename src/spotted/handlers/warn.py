"""/warn command"""
from telegram import Update
from telegram.ext import CallbackContext
from spotted.data import Config, User
from spotted.utils import EventInfo


async def warn_cmd(update: Update, context: CallbackContext):
    """Handles the /warn command.
    Warn a user by replying to one of his message in the comment group with /warn

    Args:
        update: update event
        context: context passed by the handler
    """
    info = EventInfo.from_message(update, context)
    g_message = update.message.reply_to_message
    if g_message is None:
        await info.bot.send_message(
            chat_id=info.chat_id,
            text="Per warnare qualcuno, rispondi al suo commento con /warn",
        )
        return
    user = User(g_message.from_user.id)
    n_warns = user.get_n_warns()
    text = f"L'utente {g_message.from_user.name} "
    if n_warns < 2:
        user.warn()
        text += f"ha ricevuto {n_warns + 1} warn(s)"
    else:
        text += "è stato bannato."
        await info.bot.ban_chat_member(Config.post_get("community_group_id"), user.user_id)
        user.ban()
    await info.bot.send_message(chat_id=info.chat_id, text=text)
