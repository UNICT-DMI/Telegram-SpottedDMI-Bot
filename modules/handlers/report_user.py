"""/report command"""
from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler, CommandHandler, MessageHandler, filters
from modules.data import Report
from modules.utils import EventInfo, conv_cancel
from modules.data import Config
from .constants import CHAT_PRIVATE_ERROR, INVALID_MESSAGE_TYPE_ERROR

STATE = {"reporting_user": 1, "reporting_user_reason": 2, "end": -1}


def report_user_conv_handler() -> ConversationHandler:
    """Creates the /report (user) conversation handler.
    The states are:

    - reporting_user: submit the username to report. Expects text starting with @ and without spaces in between
    - reporting_user_reason: submit the reason of the report. Expects text

    Returns:
        conversation handler
    """
    return ConversationHandler(
        entry_points=[CommandHandler("report", report_cmd)],
        states={
            STATE["reporting_user"]: [
                MessageHandler(~filters.COMMAND & ~filters.UpdateType.EDITED_MESSAGE, report_user_msg)
            ],
            STATE["reporting_user_reason"]: [
                MessageHandler(~filters.COMMAND & ~filters.UpdateType.EDITED_MESSAGE, report_user_sent_msg)
            ],
        },
        fallbacks=[CommandHandler("cancel", conv_cancel("report"))],
        allow_reentry=False,
    )


async def report_cmd(update: Update, context: CallbackContext) -> int:
    """Handles the reply to the key "Report".
    Checks the message the user wants to report

    Args:
        update: update event
        context: context passed by the handler

    Returns:
        next state of the conversation
    """
    info = EventInfo.from_message(update, context)
    if not info.is_private_chat:  # you can only post with a private message
        await info.bot.send_message(chat_id=info.chat_id, text=CHAT_PRIVATE_ERROR)
        return STATE["end"]

    user_report = Report.get_last_user_report(user_id=info.user_id)

    if user_report is not None:
        minutes_elapsed = user_report.minutes_passed
        remain_minutes = int(Config.post_get("report_wait_mins") - minutes_elapsed)

        if remain_minutes > 0:
            await info.bot.send_message(chat_id=info.chat_id, text=f"Aspetta {remain_minutes} minuti")
            return STATE["end"]

    await info.bot.send_message(chat_id=info.chat_id, text="Invia l'username di chi vuoi segnalare. Es. @massimobene")

    return STATE["reporting_user"]


async def report_user_msg(update: Update, context: CallbackContext) -> int:
    """Handles the reply to the /report command after sent the @username.
    Checks the the user wants to report, and goes to ask the reason

    Args:
        update: update event
        context: context passed by the handler

    Returns:
        next state of the conversation
    """
    info = EventInfo.from_message(update, context)
    reported_user = info.text.strip()
    if not info.is_valid_message_type or not reported_user.startswith("@") or " " in reported_user:
        await info.bot.send_message(
            chat_id=info.chat_id,
            text="Questo tipo di messaggio non è supportato\n"
            "È consentito solo username telegram. Puoi annullare il processo con /cancel",
        )
        return STATE["reporting_user"]

    if context.user_data is None:
        return STATE["end"]

    context.user_data["current_report_target"] = reported_user

    await info.bot.send_message(
        chat_id=info.chat_id,
        text="Scrivi il motivo della tua segnalazione.\n"
        "Cerca di essere esaustivo, potrai inviare un altro report "
        f"dopo {Config.post_get('report_wait_mins')} minuti.\n"
        "Puoi annullare il processo con /cancel",
    )

    return STATE["reporting_user_reason"]


async def report_user_sent_msg(update: Update, context: CallbackContext) -> int:
    """Handles the reply to the /report command after sent the reason.
    Checks the the user wants to report, and goes to final step

    Args:
        update: update event
        context: context passed by the handler

    Returns:
        next state of the conversation
    """
    info = EventInfo.from_message(update, context)
    if not info.is_valid_message_type:  # the type is NOT supported
        await info.bot.send_message(chat_id=info.chat_id, text=INVALID_MESSAGE_TYPE_ERROR)
        return STATE["reporting_user_reason"]

    if context.user_data is None or "current_report_target" not in context.user_data:
        return STATE["end"]

    target_username = context.user_data["current_report_target"]

    chat_id = Config.post_get("group_id")  # should be admin group
    admin_message = await info.bot.sendMessage(
        chat_id=chat_id, text="🚨🚨 SEGNALAZIONE 🚨🚨\n\n" + "Username: " + target_username + "\n\n" + info.text
    )

    await info.bot.send_message(
        chat_id=info.chat_id, text="Gli admins verificheranno quanto accaduto. Grazie per la collaborazione!"
    )

    Report.create_user_report(user_id=info.user_id, target_username=target_username, admin_message=admin_message)

    return STATE["end"]
