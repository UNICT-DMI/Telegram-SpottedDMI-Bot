"""Common info needed in both command and callback handlers"""
from telegram import Update, Message
from telegram.ext import CallbackContext


def get_message_info(update: Update, context: CallbackContext) -> dict:
    """Get the classic info from the update and context parameters for commands and messages

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler

    Returns:
        dict: {bot, chat_id, text, message_id, sender_id}
    """
    return {
        'bot': context.bot,
        'chat_id': update.message.chat_id,
        'text': update.message.text,
        'message_id': update.message.message_id,
        'sender_id': update.message.from_user.id
    }


def get_callback_info(update: Update, context: CallbackContext) -> dict:
    """Get the classic info from the update and context parameters for callbacks

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler

    Returns:
        dict: {bot, bot_data, message, chat_id, text, query_id, data, message_id, sender_id, sender_username, reply_markup, 'user_data'}
    """
    return {
        'bot': context.bot,
        'bot_data': context.bot_data,
        'message': update.callback_query.message,
        'chat_id': update.callback_query.message.chat_id,
        'text': update.callback_query.message.text,
        'query_id': update.callback_query.id,
        'data': update.callback_query.data,
        'message_id': update.callback_query.message.message_id,
        'sender_id': update.callback_query.from_user.id,
        'sender_username': update.callback_query.from_user.username,
        'reply_markup': update.callback_query.message.reply_markup,
        'user_data': context.user_data
    }


def get_job_info(context: CallbackContext) -> dict:
    """Get the classic info from the context parameter for jobs

    Args:
        context (CallbackContext): context passed by the handler

    Returns:
        dict: {bot}
    """
    return {
        'bot': context.bot,
    }


def check_message_type(message: Message) -> bool:
    """Check that the type of the message is one of the ones supported

    Args:
        message (Message): message to check

    Returns:
        bool: whether its type is supported or not
    """
    return message.text or message.photo or message.voice or message.audio\
    or message.video or message.animation or message.sticker or message.poll
