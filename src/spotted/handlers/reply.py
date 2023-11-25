"""/reply command"""
from telegram import Update
from telegram.ext import CallbackContext

from spotted.data import PendingPost, Report
from spotted.utils import EventInfo


async def reply_cmd(update: Update, context: CallbackContext):
    """Handles the /reply command.
    Send a message to a user by replying to one of his pending posts with /reply + the message you want to send

    Args:
        update: update event
        context: context passed by the handler
    """
    info = EventInfo.from_message(update, context)

    if len(info.text) <= 7:  # the reply is empty
        await info.bot.send_message(
            chat_id=info.chat_id,
            text="La reply è vuota\n"
            "Per mandare un messaggio ad un utente, rispondere al suo post o report con /reply "
            "seguito da ciò che gli si vuole dire",
        )
        return

    g_message_id = update.message.reply_to_message.message_id
    if (pending_post := PendingPost.from_group(admin_group_id=info.chat_id, g_message_id=g_message_id)) is not None:
        await info.bot.send_message(
            chat_id=pending_post.user_id,
            text="COMUNICAZIONE DEGLI ADMIN SUL TUO ULTIMO POST:\n" + info.text[7:].strip(),
        )
    elif (report := Report.from_group(admin_group_id=info.chat_id, g_message_id=g_message_id)) is not None:
        await info.bot.send_message(
            chat_id=report.user_id, text="COMUNICAZIONE DEGLI ADMIN SUL TUO ULTIMO REPORT:\n" + info.text[7:].strip()
        )
    else:  # the reply does not refer to a pending post or a report
        await info.bot.send_message(
            chat_id=info.chat_id,
            text="Il messaggio selezionato non è valido.\n"
            "Per mandare un messaggio ad un utente, rispondere al suo post o report con /reply "
            "seguito da ciò che gli si vuole dire",
        )
        return

    await info.bot.send_message(
        chat_id=info.chat_id, text="L'utente ha ricevuto il messaggio", reply_to_message_id=g_message_id
    )
