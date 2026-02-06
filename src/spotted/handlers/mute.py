"""/mute command"""

from telegram import Update
from telegram.ext import CallbackContext

from spotted.data import Config, User
from spotted.utils import EventInfo


async def mute_cmd(update: Update, context: CallbackContext):
    """Handles the /mute command.
    Mute a user by replying to one of his message in the comment group with /mute <n_days>
    Args:
        update: update event
        context: context passed by the handler
    """
    info = EventInfo.from_message(update, context)
    admins = [admin.user.id for admin in await info.bot.get_chat_administrators(Config.post_get("community_group_id"))]
    g_message = update.message.reply_to_message
    if (info.user_id not in admins) or (g_message is None):
        text = "Per mutare rispondi ad un commento con /mute <days>\nIl numero di giorni è opzionale, di default è 7"
        if info.user_id not in admins:
            text = "Non sei un admin"
        await info.bot.send_message(chat_id=info.user_id, text=text)
        await info.message.delete()
        return
    days = Config.post_get("mute_default_duration_days")
    if len(context.args) > 0:
        try:
            days = int(context.args[0])
        except ValueError:
            pass
    user = User(g_message.from_user.id)
    mute_days_text = f"{days} giorn{'o' if days == 1 else 'i'}"
    await user.mute(info.bot, days)
    await info.bot.send_message(
        chat_id=Config.post_get("admin_group_id"),
        text=f"L'utente {user.user_id} è stato mutato per {mute_days_text}.",
    )
    await info.bot.send_message(chat_id=user.user_id, text=f"Sei stato mutato da Spotted DMI per {mute_days_text}.")
    await info.message.delete()
