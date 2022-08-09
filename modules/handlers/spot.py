"""/spot command"""
from random import choice
from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from modules.data import User
from modules.utils import EventInfo, conv_cancel, get_confirm_kb, get_preview_kb
from modules.handlers.constants import CHAT_PRIVATE_ERROR, INVALID_MESSAGE_TYPE_ERROR
from modules.data import Config
from modules.data.data_reader import read_md

STATE = {'posting': 1, 'confirm': 2, 'end': -1}


def spot_conv_handler() -> ConversationHandler:
    """Creates the spot conversation handler.
    The states are:

    - posting: submit the spot. Expects text, photo or many other formats
    - confirm: confirm or cancel the spot submission. Expects an inline query

    Returns:
        conversaton handler
    """
    return ConversationHandler(
        entry_points=[CommandHandler("spot", spot_cmd)],
        states={
            STATE['posting']: [MessageHandler(~Filters.command & ~Filters.update.edited_message, spot_msg),
                               CallbackQueryHandler(spot_preview_query, pattern=r"^meme_preview,.+")],
            STATE['confirm']: [CallbackQueryHandler(spot_confirm_query, pattern=r"^meme_confirm,.+")],
        },
        fallbacks=[CommandHandler("cancel", conv_cancel("spot"))],
        allow_reentry=False)


def spot_cmd(update: Update, context: CallbackContext) -> int:
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
        info.bot.send_message(chat_id=info.chat_id, text=CHAT_PRIVATE_ERROR)
        return STATE['end']

    if user.is_banned:  # the user is banned
        info.bot.send_message(chat_id=info.chat_id, text="Sei stato bannato 😅")
        return STATE['end']

    if user.is_pending:  # there is already a post in pending
        info.bot.send_message(chat_id=info.chat_id, text="Hai già un post in approvazione 🧐")
        return STATE['end']

    info.bot.send_message(chat_id=info.chat_id, text="Invia il post che vuoi pubblicare")
    return STATE['posting']


def spot_msg(update: Update, context: CallbackContext) -> int:
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
        info.bot.send_message(chat_id=info.chat_id, text=INVALID_MESSAGE_TYPE_ERROR)
        return STATE['posting']

    if info.message.entities:
        types = [entity.type for entity in info.message.entities]

        if "url" in types or "text_link" in types:
            info.bot.send_message(chat_id=info.chat_id,
                                  text="Il post contiene link, vuoi pubblicare con l'anteprima?",
                                  reply_to_message_id=info.message_id,
                                  reply_markup=get_preview_kb())
            return STATE['posting']

    info.bot.send_message(chat_id=info.chat_id,
                          text="Sei sicuro di voler pubblicare questo post?",
                          reply_to_message_id=info.message_id,
                          reply_markup=get_confirm_kb())
    return STATE['confirm']


def spot_preview_query(update: Update, context: CallbackContext) -> int:
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
    info.user_data['preview'] = arg == "accept"
    info.bot.edit_message_text(chat_id=info.chat_id,
                                message_id=info.message_id,
                                text="Sei sicuro di voler pubblicare questo post?",
                                reply_markup=get_confirm_kb())
    return STATE['confirm']


def spot_confirm_query(update: Update, context: CallbackContext) -> int:
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
        elif info.send_post_to_admins():
            text = "Il tuo post è in fase di valutazione\n"\
                f"Una volta pubblicato, lo potrai trovare su {Config.meme_get('channel_tag')}"
        else:
            text = "Si è verificato un problema\nAssicurati che il tipo di post sia fra quelli consentiti"

    elif arg == "cancel":  # if the the user changed his mind
        text = choice(read_md("no_strings").split("\n"))

    info.bot.edit_message_text(chat_id=info.chat_id, message_id=info.message_id, text=text)
    return STATE['end']
