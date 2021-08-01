"""report callback"""
from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram.error import Unauthorized
from modules.data import Report
from modules.utils import EventInfo, conv_cancel
from modules.handlers.constants import INVALID_MESSAGE_TYPE_ERROR
from modules.data import config_map

STATE = {'reporting_spot': 1, 'end': -1}


def report_spot_conv_handler() -> CommandHandler:
    """Creates the report (user) conversation handler.
    The states are:

    - reporting_spot: submit the reason of the report. Expects text

    Returns:
        conversaton handler
    """
    return ConversationHandler(entry_points=[CallbackQueryHandler(report_spot_callback, pattern=r"^meme_report\.*")],
                               states={
                                   STATE['reporting_spot']: [MessageHandler(~Filters.command, report_spot_msg)],
                               },
                               fallbacks=[CommandHandler("cancel", conv_cancel("report"))],
                               allow_reentry=False,
                               per_chat=False)


def report_spot_callback(info: EventInfo, args: str) -> int:  # pylint: disable=unused-argument
    """Handles the report callback.

    Args:
        info (dict): information about the callback
        arg (str): unused

    Returns:
        int: new conversation state
    """
    abusive_message_id = info.message.reply_to_message.message_id

    report = Report.get_post_report(user_id=info.user_id, channel_id=info.chat_id, c_message_id=abusive_message_id)
    if report is not None:  # this user has already reported this post
        info.answer_callback_query(text="Hai già segnalato questo spot.")
        return STATE['end']
    try:
        info.bot.forward_message(chat_id=info.user_id, from_chat_id=info.chat_id, message_id=abusive_message_id)
        info.bot.send_message(chat_id=info.user_id,
                              text="Scrivi il motivo della segnalazione del post, altrimenti digita /cancel")
        info.answer_callback_query(text="Segnala in privato tramite il bot")
    except Unauthorized:
        info.answer_callback_query(text=f"Assicurati di aver avviato la chat con {config_map['bot_tag']}")
        return STATE['end']

    info.user_data['current_post_reported'] = f"{info.chat_id},{abusive_message_id}"
    return STATE['reporting_spot']


def report_spot_msg(update: Update, context: CallbackContext) -> int:
    """Handles the reply to the key "Report".
    Checks the message the user wants to report, and goes to the final step

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler

    Returns:
        int: next state of the conversation
    """
    info = EventInfo.from_message(update, context)

    if not info.is_private_chat:
        return STATE['reporting_spot']

    if not info.is_valid_message_type:  # the type is NOT supported
        info.bot.send_message(chat_id=info.chat_id, text=INVALID_MESSAGE_TYPE_ERROR)
        return STATE['reporting_spot']

    chat_id = config_map['meme']['group_id']  # should be admin group

    channel_id, target_message_id = context.user_data['current_post_reported'].split(",")

    info.bot.forward_message(chat_id=chat_id, from_chat_id=channel_id, message_id=target_message_id)
    admin_message = info.bot.sendMessage(chat_id=chat_id, text="🚨🚨 SEGNALAZIONE 🚨🚨\n\n" + info.text)
    info.bot.send_message(chat_id=info.chat_id,
                          text="Gli admins verificheranno quanto accaduto. Grazie per la collaborazione!")

    Report.create_post_report(user_id=info.user_id,
                              channel_id=channel_id,
                              c_message_id=target_message_id,
                              admin_message=admin_message)

    return STATE['end']
