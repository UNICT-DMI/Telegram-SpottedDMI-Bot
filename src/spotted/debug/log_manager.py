"""Handles the logging of events"""
import html
import logging
import traceback
from datetime import datetime
from pathlib import Path

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext

from spotted.data import Config

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


async def error_handler(update: Update, context: CallbackContext):
    """Logs the error and notifies the admins.

    Args:
        update: update event
        context: context passed by the handler
    """
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

    traceback_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    traceback_str = "".join(traceback_list)

    min_traceback_list = [line for line in traceback_list if "modules" in line]
    min_traceback_list.append(traceback_list[-1])
    min_traceback_str = "".join(min_traceback_list)
    await notify_error_admin(context=context, traceback_str=min_traceback_str)

    try:  # log the error
        log_file_path = Path(Config.debug_get("log_error_file"))
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_file_path, "a", encoding="utf8") as log_file:
            message = (
                "\n___ERROR LOG___\n"
                f"time: {datetime.now()}\n"
                f"error: {context.error}\n"
                f"error_traceback: {traceback_str}\n"
            )
            if update and update.message:  # if the update contains a message, show additional info
                chat = update.message.chat
                message += (
                    f"id_message:  {update.message.message_id}\n"
                    f"chat_id:  {chat.id}\n"
                    f"chat_type:  {chat.type}\n"
                    f"chat_title:  {chat.title}\n"
                    f"message_date:  {update.message.date}\n"
                )
            message += "_____________\n"
            log_file.write("\n" + message)
    except AttributeError as ex:
        logger.warning(ex)
    except FileNotFoundError as ex:
        logger.error(ex)


async def notify_error_admin(context: CallbackContext, traceback_str: str):
    """Sends a telegram message to notify the admins.

    Args:
        context: context passed by the handler
        traceback_str: the traceback text
    """
    traceback_str = traceback_str.replace(Config.settings_get("token"), "[bot_token]")
    text = f"An exception was raised:\n" f"<pre>{html.escape(traceback_str)}</pre>"
    await context.bot.send_message(chat_id=Config.post_get("admin_group_id"), text=text, parse_mode=ParseMode.HTML)


async def log_message(update: Update, _: CallbackContext):
    """Log the message that caused the update

    Args:
        update: update event
        context: context passed by the handler
    """
    if update.message:
        try:
            log_file_path = Path(Config.debug_get("log_file"))
            log_file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_file_path, "a", encoding="utf8") as log_file:
                user = update.message.from_user
                chat = update.message.chat
                message = (
                    f"\n___ID MESSAGE:  {str(update.message.message_id)} ____\n"
                    "___INFO USER___\n"
                    f"user_id:  {str(user.id)}\n"
                    f"user_name:  {str(user.username)}\n"
                    f"user_first_lastname: {str(user.first_name)} {str(user.last_name)}\n"
                    "___INFO CHAT___\n"
                    f"chat_id:  {str(chat.id)}\n"
                    f"chat_type:  {str(chat.type)}\n"
                    f"chat_title:  {str(chat.title)}\n"
                    "___TESTO___\n"
                    f"text:  {str(update.message.text)}\n"
                    f"date:  {str(update.message.date)}"
                    "\n_____________\n"
                )
                log_file.write("\n" + message)
        except AttributeError as ex:
            logger.warning(ex)
        except FileNotFoundError as ex:
            logger.error(ex)
