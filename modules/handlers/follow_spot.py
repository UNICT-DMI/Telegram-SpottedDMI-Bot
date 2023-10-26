import logging
from telegram import Update
from telegram.ext import CallbackContext
from telegram.error import Unauthorized
from modules.utils import EventInfo
from modules.data import Config
from modules.data.db_manager import DbManager


logger = logging.getLogger(__name__)

def follow_spot_callback(update: Update, context: CallbackContext) -> int:
    """Handles the follow callback.

    Args:
        update: update event
        context: context passed by the handler

    Returns:
        next state of the conversation
    """
    info = EventInfo.from_callback(update, context)
    message_id = info.message.reply_to_message.message_id if Config.meme_get('comments') else info.message_id

    # Check if user is already following this spot
    is_following: bool = len(DbManager.select_from(
        table_name = "user_follow",
        select = "*",
        where = "user_id = %s and message_id = %s",
        where_args = (info.user_id, message_id)
    )) > 0

    if is_following:
        answer_text = "Non stai più seguendo questo spot."
        # Forget the stored data
        DbManager.delete_from(
            table_name="user_follow",
            where="user_id = %s and message_id = %s",
            where_args=(info.user_id, message_id)
        )
        
        info.bot.send_message(
            chat_id = info.user_id,
            text = "Non stai più seguendo questo spot.",
            reply_to_message_id = message_id,
            disable_notification = True
        )
    else:
        answer_text = "Stai seguendo questo spot."
        try:
            # Forward the spot in user's conversation with the bot, so that
            # future comments will be sent in response to this forwarded message.
            private_message = info.bot.forward_message(
                chat_id = info.user_id,
                from_chat_id = info.chat_id,
                message_id = message_id,
                disable_notification = True
            )

            # Add an explanation to why the message was forwarded?
            info.bot.send_message(
                chat_id = info.user_id,
                text = "Stai seguendo questo spot.",
                reply_to_message_id = private_message.message_id
            )
        except Unauthorized:
            info.answer_callback_query(text=f"Assicurati di aver avviato la chat con {Config.settings_get('bot_tag')}")
            return -1

        # Remember the user_id and message_id
        DbManager.insert_into(
            table_name="user_follow",
            columns=("user_id", "message_id", "private_message_id"),
            values=(info.user_id, message_id, private_message.message_id)
        )

    info.answer_callback_query(text=answer_text)
    return -1