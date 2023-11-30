"""/mute command"""
import re

from telegram import Update
from telegram.ext import CallbackContext

from spotted.data import User
from spotted.utils import EventInfo


async def mute_cmd(update: Update, context: CallbackContext):
    """Handles the /mute command.
    Mute a user by replying to one of his message in the comment group with /mute <n_days>

    Args:
        update: update event
        context: context passed by the handler
    """
    info = EventInfo.from_message(update, context)
    g_message = update.message.reply_to_message
    user = User(g_message.from_user.id)
    match = re.search(r"^/mute (?P<days>\\d*)$", info.text)

    if g_message is None or match is None:
        await info.bot.send_message(
            chat_id=info.chat_id,
            text="Per mutare qualcuno, rispondi al suo commento con /mute <giorni>",
        )
        return

    days = 1 if match == "" else int(match)  # if no argv is provided, default is 1 day

    user.mute(info.bot, days)
    text = f"L'utente è stato mutato per {days} giorn{'o' if days == 1 else 'i'}."
    await info.bot.send_message(chat_id=info.chat_id, text=text)
