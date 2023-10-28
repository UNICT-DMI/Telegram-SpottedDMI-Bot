"Handles callback when the 'Follow Spot' button is clicked."
import logging
from telegram import Update
from telegram.ext import CallbackContext
from telegram.error import Unauthorized
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
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
    result = DbManager.select_from(
        table_name = "user_follow",
        select = "private_message_id",
        where = "user_id = %s and message_id = %s",
        where_args = (info.user_id, message_id)
    )
    
    if len(result) > 0:
        answer_text = "Non stai più seguendo questo spot."
        # Forget the stored data
        DbManager.delete_from(
            table_name="user_follow",
            where="user_id = %s and message_id = %s",
            where_args=(info.user_id, message_id)
        )

        info.bot.send_message(
            chat_id = info.user_id,
            text = answer_text,
            reply_to_message_id = result[0]['private_message_id'],
            disable_notification = True
        )
    else:
        post_url = f"https://t.me/c/{str(info.chat_id).replace('-100', '')}/{info.message_id}"
        answer_text = "Stai seguendo questo spot."
        try:
            # Forward the spot in user's conversation with the bot, so that
            # future comments will be sent in response to this forwarded message.
            private_message = info.bot.copy_message(
                chat_id = info.user_id,
                from_chat_id = info.chat_id,
                message_id = message_id,
                disable_notification = True,
                reply_markup = InlineKeyboardMarkup([
                    [InlineKeyboardButton("💬 Visualizza thread", url = post_url)]
                ])
            )

            # Add an explanation to why the message was forwarded?
            info.bot.send_message(
                chat_id = info.user_id,
                text = answer_text,
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
