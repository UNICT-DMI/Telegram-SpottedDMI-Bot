"""/warn command"""
from telegram import Update
from telegram.ext import CallbackContext

from spotted.data import Config, User
from spotted.handlers.ban import execute_ban
from spotted.utils import EventInfo


async def warn_cmd(update: Update, context: CallbackContext):
    """Handles the /warn command.
    Warn a user by replying to one of his message in the comment group with /warn
    Args:
        update: update event
        context: context passed by the handler
    """
    info = EventInfo.from_message(update, context)
    admins = [admin.user.id for admin in await info.bot.get_chat_administrators(Config.post_get("community_group_id"))]
    g_message = update.message.reply_to_message
    if (info.user_id not in admins) or (g_message is None) or len(context.args) == 0:
        text = "Per warnare rispondi ad un commento con /warn <motivo>"
        if info.user_id not in admins:
            text = "Non sei un admin"
        await info.bot.send_message(chat_id=info.user_id, text=text)
        await info.message.delete()
        return
    user = User(g_message.from_user.id)
    user.warn()
    n_warns = user.get_n_warns()
    await info.bot.send_message(
        chat_id=user.user_id,
        text=f"Sei stato warnato su SpottedDMI, hai {n_warns} warn su"
        f" un massimo di {Config.post_get('max_n_warns')} in "
        f"{Config.post_get('warn_expiration_days')} giorni!\n"
        f"Raggiunto il massimo sarai bannato!\n\n\n"
        f"Motivo: {' '.join(context.args)}",
    )
    if user.is_warn_bannable:
        await execute_ban(user.user_id, info, from_warn=True)
    await info.message.delete()
