"""Handles the logging of events"""
import logging
from modules.data.data_reader import get_abs_path

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Logger enabled")


def log_message(update, context):
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
