"""Handles the logging of events"""
import logging
import traceback
import html
from datetime import datetime
from telegram import Update, ParseMode
from telegram.ext import CallbackContext
from modules.data.data_reader import config_map, get_abs_path

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Logger enabled")


def error_handler(update: Update, context: CallbackContext):  # pylint: disable=unused-argument
    """Logs the error and notifies the admins.

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler
    """
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

    traceback_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    traceback_str = ''.join(traceback_list)

    notify_error_admin(context=context, traceback_str=traceback_str)
    try:  # log the error
        with open(get_abs_path("logs", "errors.log"), "a", encoding="utf8") as log_file:
            message = "\n___ERROR LOG___\n"\
                        f"time: {datetime.now()}\n"\
                        f"error: {context.error}\n"\
                        f"error_traceback: {traceback_str}\n"
            if update and update.message:  # if the update contains a message, show additional info
                chat = update.message.chat
                message += f"id_message:  {update.message.message_id}\n"\
                            f"chat_id:  {chat.id}\n"\
                            f"chat_type:  {chat.type}\n"\
                            f"chat_title:  {chat.title}\n"\
                            f"message_date:  {update.message.date}\n"
            message += "_____________\n"
            log_file.write("\n" + message)
    except AttributeError as e:
        logger.warning(e)
    except FileNotFoundError as e:
        logger.error(e)


def notify_error_admin(context: CallbackContext, traceback_str: str):
    """Sends a telegram message to notify the admins.

    Args:
        context (CallbackContext): context passed by the handler
    """
    text = (f'An exception was raised while handling an update\n\n' f'<pre>{html.escape(traceback_str)}</pre>')
    context.bot.send_message(chat_id=config_map['meme']['group_id'], text=text, parse_mode=ParseMode.HTML)


def log_message(update, context):  # pylint: disable=unused-argument
    """Log the message that caused the update

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler
    """
    if update.message:
        try:
            with open(get_abs_path("logs", "messages.log"), "a", encoding="utf8") as log_file:

                user = update.message.from_user
                chat = update.message.chat
                message = f"\n___ID MESSAGE:  {str(update.message.message_id)} ____\n"\
                        "___INFO USER___\n"\
                        f"user_id:  {str(user.id)}\n"\
                        f"user_name:  {str(user.username)}\n"\
                        f"user_first_lastname: {str(user.first_name)} {str(user.last_name)}\n"\
                        "___INFO CHAT___\n"\
                        f"chat_id:  {str(chat.id)}\n"\
                        f"chat_type:  {str(chat.type)}\n"\
                        f"chat_title:  {str(chat.title)}\n"\
                        "___TESTO___\n"\
                        f"text:  {str(update.message.text)}\n"\
                        f"date:  {str(update.message.date)}"\
                        "\n_____________\n"
                log_file.write("\n" + message)
        except AttributeError as e:
            logger.warning(e)
        except FileNotFoundError as e:
            logger.error(e)
