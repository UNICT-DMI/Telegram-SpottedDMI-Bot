"""/rules command"""
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext

from spotted.data import read_md
from spotted.utils import EventInfo


async def rules_cmd(update: Update, context: CallbackContext):
    """Handles the /rules command.
    Sends a message containing the rules

    Args:
        update: update event
        context: context passed by the handler
    """
    info = EventInfo.from_message(update, context)
    text = read_md("rules")
    await info.bot.send_message(
        chat_id=info.chat_id, text=text, parse_mode=ParseMode.MARKDOWN_V2, disable_web_page_preview=True
    )
