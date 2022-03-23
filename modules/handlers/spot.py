"""/spot command"""
from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from modules.data import User
from modules.utils import EventInfo, conv_cancel, get_confirm_kb
from modules.handlers.constants import CHAT_PRIVATE_ERROR, INVALID_MESSAGE_TYPE_ERROR
from modules.data import Config

STATE = {'posting': 1, 'confirm': 2, 'end': -1}


def spot_conv_handler() -> CommandHandler:
    """Creates the spot conversation handler.
    The states are:

    - posting: submit the spot. Expects text, photo or many other formats
    - confirm: confirm or cancel the spot submission. Expects an inline query

    Returns:
        conversaton handler
    """
    return ConversationHandler(entry_points=[CommandHandler("spot", spot_cmd)],
                               states={
                                   STATE['posting']: [MessageHandler(~Filters.command, spot_msg)],
                                   STATE['confirm']: [CallbackQueryHandler(spot_confirm_query, pattern=r"^meme_confirm,.+")]
                               },
                               fallbacks=[CommandHandler("cancel", conv_cancel("spot"))],
                               allow_reentry=False)


def spot_cmd(update: Update, context: CallbackContext) -> int:
    """Handles the /spot command.
    Checks that the user is in a private chat and it's not banned and start the post conversation

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler

    Returns:
        int: next state of the conversation
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
        update (Update): update event
        context (CallbackContext): context passed by the handler

    Returns:
        int: next state of the conversation
    """
    info = EventInfo.from_message(update, context)

    if not info.is_valid_message_type:  # the type is NOT supported
        info.bot.send_message(chat_id=info.chat_id, text=INVALID_MESSAGE_TYPE_ERROR)
        return STATE['posting']

    info.bot.send_message(chat_id=info.chat_id,
                          text="Sei sicuro di voler publicare questo post?",
                          reply_to_message_id=info.message_id,
                          reply_markup=get_confirm_kb())
    return STATE['confirm']


def spot_confirm_query(update: Update, context: CallbackContext):
    """Handles the [ submit | cancel ] callback.
    Creates the bid or cancels its creation.

    - submit: saves the post as pending and sends it to the admins for them to check.
    - cancel: cancels the current spot conversation

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler

    Returns:
        int: next state of the conversation
    """
    info = EventInfo.from_callback(update, context)
    arg = info.query_data.split(",")[1]
    if arg == "submit":  # if the the user wants to publish the post
        if User(info.user_id).is_pending:  # there is already a spot in pending by this user
            text = "Hai già un post in approvazione 🧐"
        elif info.send_post_to_admins():
            text = "Il tuo post è in fase di valutazione\n"\
                f"Una volta pubblicato, lo potrai trovare su {Config.meme_get('channel_tag')}"
        else:
            text = "Si è verificato un problema\nAssicurati che il tipo di post sia fra quelli consentiti"

    elif arg == "cancel":  # if the the user changed his mind
        text = "Va bene, alla prossima 🙃"

    info.bot.edit_message_text(chat_id=info.chat_id, message_id=info.message_id, text=text)
    return STATE['end']
