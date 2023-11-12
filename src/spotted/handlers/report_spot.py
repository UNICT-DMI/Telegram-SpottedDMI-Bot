"""report callback"""
from telegram import Update
from telegram.ext import (
    CallbackContext,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from telegram.error import Forbidden
from spotted.data import Report
from spotted.utils import EventInfo, conv_cancel
from spotted.data import Config
from .constants import INVALID_MESSAGE_TYPE_ERROR

STATE = {"reporting_spot": 1, "end": -1}


def report_spot_conv_handler() -> ConversationHandler:
    """Creates the report (user) conversation handler.
    The states are:

    - reporting_spot: submit the reason of the report. Expects text

    Returns:
        conversation handler
    """
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(report_spot_callback, pattern=r"^report\.*")],
        states={
            STATE["reporting_spot"]: [
                MessageHandler(~filters.COMMAND & ~filters.UpdateType.EDITED_MESSAGE, report_spot_msg)
            ],
        },
        fallbacks=[CommandHandler("cancel", conv_cancel("report"))],
        allow_reentry=False,
        per_chat=False,
    )


async def report_spot_callback(update: Update, context: CallbackContext) -> int:
    """Handles the report callback.

    Args:
        update: update event
        context: context passed by the handler

    Returns:
        next state of the conversation
    """
    info = EventInfo.from_callback(update, context)
    abusive_message_id = info.message.reply_to_message.message_id if Config.post_get("comments") else info.message_id

    report = Report.get_post_report(user_id=info.user_id, channel_id=info.chat_id, c_message_id=abusive_message_id)
    if report is not None:  # this user has already reported this post
        await info.answer_callback_query(text="Hai già segnalato questo spot")
        return STATE["end"]
    try:
        await info.bot.forward_message(chat_id=info.user_id, from_chat_id=info.chat_id, message_id=abusive_message_id)
        await info.bot.send_message(
            chat_id=info.user_id, text="Scrivi il motivo della segnalazione del post, altrimenti digita /cancel"
        )
        await info.answer_callback_query(text="Segnala in privato tramite il bot")
    except Forbidden:
        await info.answer_callback_query(
            text=f"Assicurati di aver avviato la chat con {Config.settings_get('bot_tag')}"
        )
        return STATE["end"]

    info.user_data["current_post_reported"] = f"{info.chat_id},{abusive_message_id}"
    return STATE["reporting_spot"]


async def report_spot_msg(update: Update, context: CallbackContext) -> int:
    """Handles the reply to the key "Report".
    Checks the message the user wants to report, and goes to the final step

    Args:
        update: update event
        context: context passed by the handler

    Returns:
        next state of the conversation
    """
    info = EventInfo.from_message(update, context)

    if not info.is_private_chat:
        return STATE["reporting_spot"]

    if not info.is_valid_message_type:  # the type is NOT supported
        await info.bot.send_message(chat_id=info.chat_id, text=INVALID_MESSAGE_TYPE_ERROR)
        return STATE["reporting_spot"]

    if context.user_data is None or "current_post_reported" not in context.user_data:
        return STATE["end"]

    chat_id = Config.post_get("group_id")  # should be admin group
    channel_id, target_message_id = context.user_data["current_post_reported"].split(",")

    await info.bot.forward_message(chat_id=chat_id, from_chat_id=channel_id, message_id=target_message_id)
    admin_message = await info.bot.sendMessage(chat_id=chat_id, text="🚨🚨 SEGNALAZIONE 🚨🚨\n\n" + info.text)
    await info.bot.send_message(
        chat_id=info.chat_id, text="Gli admins verificheranno quanto accaduto. Grazie per la collaborazione!"
    )

    Report.create_post_report(
        user_id=info.user_id, channel_id=channel_id, c_message_id=target_message_id, admin_message=admin_message
    )

    return STATE["end"]
