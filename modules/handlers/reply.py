"""/reply command"""
from telegram import Update
from telegram.ext import CallbackContext
from modules.data import config_map, PendingPost, Report
from modules.utils import EventInfo


def reply_cmd(update: Update, context: CallbackContext):
    """Handles the /reply command.
    Send a message to a user by replying to one of his pending posts with /reply + the message you want to send

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler
    """
    info = EventInfo.from_message(update, context)
    if info.chat_id == config_map['meme']['group_id']:  # you have to be in the admin group

        if len(info.text) <= 7:  # the reply is empty
            info.bot.send_message(
                chat_id=info.chat_id,
                text="La reply è vuota\n"\
                "Per mandare un messaggio ad un utente, rispondere al suo post o report con /reply "\
                "seguito da ciò che gli si vuole dire"
            )
            return

        g_message_id = update.message.reply_to_message.message_id

        pending_post = PendingPost.from_group(group_id=info.chat_id, g_message_id=g_message_id)
        if pending_post is not None:  # the message was a pending post
            info.bot.send_message(chat_id=pending_post.user_id,
                                  text="COMUNICAZIONE DEGLI ADMIN SUL TUO ULTIMO POST:\n" + info.text[7:].strip())
            info.bot.send_message(chat_id=info.chat_id,
                                    text="L'utente ha ricevuto il seguente messaggio:\n"\
                                        "COMUNICAZIONE DEGLI ADMIN SUL TUO ULTIMO POST:\n" + info.text[7:].strip(),
                                    reply_to_message_id=g_message_id)
            return
        report = Report.from_group(group_id=info.chat_id, g_message_id=g_message_id)
        if report is not None:  # the message was a report
            info.bot.send_message(chat_id=report.user_id,
                                  text="COMUNICAZIONE DEGLI ADMIN SUL TUO ULTIMO REPORT:\n" + info.text[7:].strip())
            info.bot.send_message(chat_id=info.chat_id,
                                    text="L'utente ha ricevuto il seguente messaggio:\n"\
                                        "COMUNICAZIONE DEGLI ADMIN SUL TUO ULTIMO REPORT:\n" + info.text[7:].strip(),
                                    reply_to_message_id=g_message_id)
            return

        info.bot.send_message(
                chat_id=info.chat_id,
                text="Il messaggio selezionato non è valido.\n"\
                "Per mandare un messaggio ad un utente, rispondere al suo post o report con /reply "\
                "seguito da ciò che gli si vuole dire"
            )
