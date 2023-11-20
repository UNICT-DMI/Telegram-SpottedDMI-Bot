"""/help command"""
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext

from spotted.data import Config, read_md
from spotted.utils import EventInfo


async def help_cmd(update: Update, context: CallbackContext):
    """Handles the /help command.
    Sends an help message

    Args:
        update: update event
        context: context passed by the handler
    """
    info = EventInfo.from_message(update, context)
    if info.chat_id == Config.post_get("admin_group_id"):  # if you are in the admin group
        text = read_md("instructions")
    else:  # you are NOT in the admin group
        text = read_md("help")
    await info.bot.send_message(
        chat_id=info.chat_id, text=text, parse_mode=ParseMode.MARKDOWN_V2, disable_web_page_preview=True
    )
