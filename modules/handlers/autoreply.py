"""/autoreply command"""
from telegram import Update
from telegram.ext import CallbackContext
from modules.data import PendingPost, Report, read_md
from modules.utils import EventInfo
from .constants import AUTOREPLIES


def autoreply_cmd(update: Update, context: CallbackContext):
    """Handles the /autoreply command.
    Send an automatic message to a user by replying to one of his pending posts with /autoreply + one of the following:
    - /autoreply gruppi materie
    - /autoreply rappresentanti
    - /autoreply repost
    - /autoreply list

    Args:
        update: update event
        context: context passed by the handler
    """
    info = EventInfo.from_message(update, context)

    arg = info.text[11:].strip().lower()
    if arg not in AUTOREPLIES or arg == "lista":
        text = read_md(AUTOREPLIES["lista"])
        info.bot.send_message(chat_id=info.chat_id, text=text)
        return

    g_message_id = update.message.reply_to_message.message_id
    user_id = None
    if (pending_post := PendingPost.from_group(group_id=info.chat_id, g_message_id=g_message_id)) is not None:
        user_id = pending_post.user_id
    elif (report := Report.from_group(group_id=info.chat_id, g_message_id=g_message_id)) is not None:
        user_id = report.user_id

    if user_id is not None:  # the message was a pending post or a report
        text = read_md(AUTOREPLIES[arg])
        info.bot.send_message(chat_id=user_id, text=f"COMUNICAZIONE DEGLI ADMIN SUL TUO ULTIMO POST:\n{text}")
        info.bot.send_message(chat_id=info.chat_id, text="L'utente ha ricevuto il messaggio", reply_to_message_id=g_message_id)
        return

    info.bot.send_message(
            chat_id=info.chat_id,
            text="Il messaggio selezionato non è valido.\n"\
                "Per mandare un messaggio ad un utente, rispondere al suo post o report con /autoreply"
        )
