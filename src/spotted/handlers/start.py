"""/start command"""
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext

from spotted.data import read_md
from spotted.utils import EventInfo


async def start_cmd(update: Update, context: CallbackContext):
    """Handles the /start command.
    Sends a welcoming message

    Args:
        update: update event
        context: context passed by the handler
    """
    info = EventInfo.from_message(update, context)
    text = read_md("start")
    await info.bot.send_message(
        chat_id=info.chat_id, text=text, parse_mode=ParseMode.MARKDOWN_V2, disable_web_page_preview=True
    )
