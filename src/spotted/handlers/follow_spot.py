"Handles callback when the 'Follow Spot' button is clicked."
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import Forbidden
from telegram.ext import CallbackContext

from spotted.data import Config
from spotted.data.user import User
from spotted.utils import EventInfo

logger = logging.getLogger(__name__)


async def follow_spot_callback(update: Update, context: CallbackContext):
    """Handles the follow callback.

    Args:
        update: update event
        context: context passed by the handler
    """
    info = EventInfo.from_callback(update, context)
    message_id = info.message.reply_to_message.message_id if Config.post_get("comments") else info.message_id

    # Get a reference to the user
    user = User(info.user_id)

    # If the user is already following this spot, there is a reference to the private message.
    # Since the user clicked the button, he wants to stop following the spot.
    if (private_message_id := user.get_follow_private_message_id(message_id)) is not None:
        answer_text = "Non stai più seguendo questo spot"
        # Forget the stored data
        user.set_follow(message_id, None)

        await info.bot.send_message(
            chat_id=info.user_id,
            text=answer_text,
            reply_to_message_id=private_message_id,
            disable_notification=True,
        )
    else:  # The user is not following this spot, so he wants to start following it.
        post_url = f"https://t.me/c/{str(info.chat_id).replace('-100', '')}/{info.message_id}"
        answer_text = "Stai seguendo questo spot"
        try:
            # Forward the spot in user's conversation with the bot, so that
            # future comments will be sent in response to this forwarded message.
            private_message = await info.bot.copy_message(
                chat_id=info.user_id,
                from_chat_id=info.chat_id,
                message_id=message_id,
                disable_notification=True,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("💬 Visualizza thread", url=post_url)]]),
            )

            # Add an explanation to why the message was forwarded?
            await info.bot.send_message(
                chat_id=info.user_id, text=answer_text, reply_to_message_id=private_message.message_id
            )
        except Forbidden:
            await info.answer_callback_query(
                text=f"Assicurati di aver avviato la chat con {Config.settings_get('bot_tag')}"
            )
            return

        # Remember the user_id and message_id
        user.set_follow(message_id, private_message.message_id)

    await info.answer_callback_query(text=answer_text)
