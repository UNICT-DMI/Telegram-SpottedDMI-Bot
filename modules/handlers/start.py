"""/start command"""
from telegram import Update, ParseMode
from telegram.ext import CallbackContext
from modules.data import read_md
from modules.utils import EventInfo

def start_cmd(update: Update, context: CallbackContext):
    """Handles the /start command.
    Sends a welcoming message

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler
    """
    info = EventInfo.from_message(update, context)
    text = read_md("start")
    info.bot.send_message(chat_id=info.chat_id, text=text, parse_mode=ParseMode.MARKDOWN_V2, disable_web_page_preview=True)
