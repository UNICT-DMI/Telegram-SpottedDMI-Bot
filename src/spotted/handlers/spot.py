"""/spot command"""
from random import choice

from telegram import Update
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from spotted.data import Config, User
from spotted.data.data_reader import read_md
from spotted.utils import EventInfo, conv_cancel, get_confirm_kb, get_preview_kb

from .constants import CHAT_PRIVATE_ERROR, INVALID_MESSAGE_TYPE_ERROR, ConversationState


def spot_conv_handler() -> ConversationHandler:
    """Creates the spot conversation handler.
    The states are:

    - posting: submit the spot. Expects text, photo or many other formats
    - confirm: confirm or cancel the spot submission. Expects an inline query

    Returns:
        conversation handler
    """
    return ConversationHandler(
        entry_points=[CommandHandler("spot", spot_cmd, filters=filters.ChatType.PRIVATE)],
        states={
            ConversationState.POSTING.value: [
                MessageHandler(~filters.COMMAND & ~filters.UpdateType.EDITED_MESSAGE, spot_msg),
            ],
            ConversationState.POSTING_PREVIEW.value: [
                CallbackQueryHandler(spot_preview_query, pattern=r"^post_preview,.+")
            ],
            ConversationState.POSTING_CONFIRM.value: [
                CallbackQueryHandler(spot_confirm_query, pattern=r"^post_confirm,.+")
            ],
        },
        fallbacks=[CommandHandler("cancel", conv_cancel("spot"))],
        allow_reentry=False,
    )


async def spot_cmd(update: Update, context: CallbackContext) -> int:
    """Handles the /spot command.
    Checks that the user is in a private chat and it's not banned and start the post conversation

    Args:
        update: update event
        context: context passed by the handler

    Returns:
        next state of the conversation
    """
    info = EventInfo.from_message(update, context)
    user = User(info.user_id)
    if not info.is_private_chat:  # you can only post from a private chat
        await info.bot.send_message(chat_id=info.chat_id, text=CHAT_PRIVATE_ERROR)
        return ConversationState.END.value

    if user.is_banned:  # the user is banned
        await info.bot.send_message(chat_id=info.chat_id, text="Sei stato bannato 😅")
        return ConversationState.END.value

    if user.is_pending:  # there is already a post in pending
        await info.bot.send_message(chat_id=info.chat_id, text="Hai già un post in approvazione 🧐")
        return ConversationState.END.value

    await info.bot.send_message(chat_id=info.chat_id, text="Invia il post che vuoi pubblicare")
    return ConversationState.POSTING.value


async def spot_msg(update: Update, context: CallbackContext) -> int:
    """Handles the reply to the /spot command.
    Checks the message the user wants to post, and goes to the final step

    Args:
        update: update event
        context: context passed by the handler

    Returns:
        next state of the conversation
    """
    info = EventInfo.from_message(update, context)

    if not info.is_valid_message_type:  # the type is NOT supported
        await info.bot.send_message(chat_id=info.chat_id, text=INVALID_MESSAGE_TYPE_ERROR)
        return ConversationState.POSTING.value

    if info.message.entities:
        types = [entity.type for entity in info.message.entities]

        if "url" in types or "text_link" in types:
            await info.bot.send_message(
                chat_id=info.chat_id,
                text="Il post contiene link, vuoi pubblicare con l'anteprima?",
                reply_to_message_id=info.message_id,
                reply_markup=get_preview_kb(),
            )
            return ConversationState.POSTING_PREVIEW.value

    await info.bot.send_message(
        chat_id=info.chat_id,
        text="Sei sicuro di voler pubblicare questo post?",
        reply_to_message_id=info.message_id,
        reply_markup=get_confirm_kb(),
    )
    return ConversationState.POSTING_CONFIRM.value


async def spot_preview_query(update: Update, context: CallbackContext) -> int:
    """Handles the [ accept | reject ] callback.
    Let the user decide if wants to post the message with or without preview.

    - accept: the post will be published with preview
    - reject: the post will be published without preview

    Args:
        update: update event
        context: context passed by the handler

    Returns:
        next state of the conversation
    """
    info = EventInfo.from_callback(update, context)
    arg = info.query_data.split(",")[1]
    info.user_data["show_preview"] = arg == "accept"
    await info.bot.edit_message_text(
        chat_id=info.chat_id,
        message_id=info.message_id,
        text="Sei sicuro di voler pubblicare questo post?",
        reply_markup=get_confirm_kb(),
    )
    return ConversationState.POSTING_CONFIRM.value


async def spot_confirm_query(update: Update, context: CallbackContext) -> int:
    """Handles the [ submit | cancel ] callback.
    Creates the bid or cancels its creation.

    - submit: saves the post as pending and sends it to the admins for them to check.
    - cancel: cancels the current spot conversation

    Args:
        update: update event
        context: context passed by the handler

    Returns:
        next state of the conversation
    """
    info = EventInfo.from_callback(update, context)
    arg = info.query_data.split(",")[1]
    text = "Qualcosa è andato storto!"
    if arg == "submit":  # if the the user wants to publish the post
        if User(info.user_id).is_pending:  # there is already a spot in pending by this user
            text = "Hai già un post in approvazione 🧐"
        elif await info.send_post_to_admins():
            text = (
                "Il tuo post è in fase di valutazione\n"
                f"Una volta pubblicato, lo potrai trovare su {Config.post_get('channel_tag')}"
            )
        else:
            text = "Si è verificato un problema\nAssicurati che il tipo di post sia fra quelli consentiti"

    elif arg == "cancel":  # if the the user changed his mind
        text = choice(read_md("no_strings").split("\n"))

    await info.bot.edit_message_text(chat_id=info.chat_id, message_id=info.message_id, text=text)
    return ConversationState.END.value
