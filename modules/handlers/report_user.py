"""/report command"""
from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler, CommandHandler, MessageHandler, Filters
from modules.data import Report
from modules.utils import EventInfo, conv_cancel
from modules.handlers.constants import CHAT_PRIVATE_ERROR, INVALID_MESSAGE_TYPE_ERROR
from modules.data import Config

STATE = {'reporting_user': 1, 'reporting_user_reason': 2, 'end': -1}


def report_user_conv_handler() -> CommandHandler:
    """Creates the /report (user) conversation handler.
    The states are:

    - reporting_user: submit the username to report. Expects text starting with @ and without spaces in between
    - reporting_user_reason: submit the reason of the report. Expects text

    Returns:
        CommandHandler: conversaton handler
    """
    return ConversationHandler(entry_points=[CommandHandler("report", report_cmd)],
                               states={
                                   STATE['reporting_user']: [MessageHandler(~Filters.command & ~Filters.update.edited_message,
                                   report_user_msg)],
                                   STATE['reporting_user_reason']: [MessageHandler(~Filters.command & ~Filters.update.edited_message,
                                   report_user_sent_msg)],
                               },
                               fallbacks=[CommandHandler("cancel", conv_cancel("report"))],
                               allow_reentry=False)


def report_cmd(update: Update, context: CallbackContext) -> int:
    """Handles the reply to the key "Report".
    Checks the message the user wants to report

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler

    Returns:
        int: next state of the conversation
    """
    info = EventInfo.from_message(update, context)
    if not info.is_private_chat:  # you can only post with a private message
        info.bot.send_message(chat_id=info.chat_id, text=CHAT_PRIVATE_ERROR)
        return STATE['end']

    user_report = Report.get_last_user_report(user_id=info.user_id)

    if user_report is not None:
        minutes_enlapsed = user_report.minutes_passed
        remain_minutes = int(Config.meme_get('report_wait_mins') - minutes_enlapsed)

        if remain_minutes > 0:
            info.bot.send_message(chat_id=info.chat_id, text=f"Aspetta {remain_minutes} minuti")
            return STATE['end']

    info.bot.send_message(chat_id=info.chat_id, text="Invia l'username di chi vuoi segnalare. Es. @massimobene")

    return STATE['reporting_user']


def report_user_msg(update: Update, context: CallbackContext) -> int:
    """Handles the reply to the /report command after sent the @username.
    Checks the the user wants to report, and goes to ask the reason

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler

    Returns:
        int: next state of the conversation
    """
    info = EventInfo.from_message(update, context)
    if not info.is_valid_message_type \
    or not info.text.startswith('@') \
    or info.text.strip().find(' ') != -1:  # the type is NOT supported
        info.bot.send_message(
            chat_id=info.chat_id,
            text="Questo tipo di messaggio non è supportato\n"\
                "È consentito solo username telegram. Puoi annullare il processo con /cancel")
        return STATE['reporting_user']

    context.user_data['current_report_target'] = info.text.strip()

    info.bot.send_message(
        chat_id=info.chat_id,
        text="Scrivi il motivo della tua segnalazione.\n"\
            "Cerca di essere esaustivo, potrai inviare un altro report "\
            f"dopo {Config.meme_get('report_wait_mins')} minuti.\n"\
            "Puoi annullare il processo con /cancel")

    return STATE['reporting_user_reason']


def report_user_sent_msg(update: Update, context: CallbackContext) -> int:
    """Handles the reply to the /report command after sent the reason.
    Checks the the user wants to report, and goes to final step

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler

    Returns:
        int: next state of the conversation
    """
    info = EventInfo.from_message(update, context)
    if not info.is_valid_message_type:  # the type is NOT supported
        info.bot.send_message(chat_id=info.chat_id, text=INVALID_MESSAGE_TYPE_ERROR)
        return STATE['reporting_user_reason']

    target_username = context.user_data['current_report_target']

    chat_id = Config.meme_get('group_id')  # should be admin group
    admin_message = info.bot.sendMessage(chat_id=chat_id,
                                         text="🚨🚨 SEGNALAZIONE 🚨🚨\n\n" + "Username: " + target_username + "\n\n" + info.text)

    info.bot.send_message(chat_id=info.chat_id,
                          text="Gli admins verificheranno quanto accaduto. Grazie per la collaborazione!")

    Report.create_user_report(user_id=info.user_id, target_username=target_username, admin_message=admin_message)

    return STATE['end']
