"""/settings command"""
from telegram import Update, ParseMode
from telegram.ext import CallbackContext
from modules.utils import EventInfo, get_settings_kb
from modules.handlers.constants import CHAT_PRIVATE_ERROR


def settings_cmd(update: Update, context: CallbackContext):
    """Handles the /settings command.
    Let's the user choose whether his posts will be credited or not

    Args:
        update: update event
        context: context passed by the handler
    """
    info = EventInfo.from_message(update, context)
    if not info.is_private_chat:  # you can only post with a private message
        info.bot.send_message(chat_id=info.chat_id, text=CHAT_PRIVATE_ERROR)
        return

    info.bot.send_message(chat_id=info.chat_id,
                          text="***Come vuoi che sia il tuo post:***",
                          reply_markup=get_settings_kb(),
                          parse_mode=ParseMode.MARKDOWN_V2)
