"""/reply command"""
from telegram import Update
from telegram.ext import CallbackContext

from spotted.data import PendingPost, Report, Config
from spotted.utils import EventInfo


async def reply_cmd(update: Update, context: CallbackContext):
    info = EventInfo.from_message(update, context)
    if len(info.args) == 0:  # the reply is empty
        await info.bot.send_message(
            chat_id=info.chat_id,
            text="La reply è vuota\n"
            "Per mandare un messaggio ad un utente, rispondere al suo post o report con /reply "
            "seguito da ciò che gli si vuole dire",
        )
        return
    ### build the reply text from the args
    reply_text = " ".join(info.args)
    g_message_id = update.message.reply_to_message.message_id
    if (pending_post := PendingPost.from_group(admin_group_id=info.chat_id, g_message_id=g_message_id)) is not None:
        await info.bot.send_message(
            chat_id=pending_post.user_id,
            text=f"COMUNICAZIONE DEGLI ADMIN SUL TUO ULTIMO POST:\n{reply_text}",
        )
    elif (report := Report.from_group(admin_group_id=info.chat_id, g_message_id=g_message_id)) is not None:
        await info.bot.send_message(
            chat_id=report.user_id, text=f"COMUNICAZIONE DEGLI ADMIN SUL TUO ULTIMO REPORT:\n{reply_text}"
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
