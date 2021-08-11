# pylint: disable=anomalous-backslash-in-string
"""Common functions needed in conversation handlers"""
from typing import Callable
from telegram import Update, ParseMode
from telegram.ext import CallbackContext
from modules.data import read_md
from modules.utils.info_util import EventInfo


def conv_fail(family: str) -> Callable:
    """Creates a function used to handle any error in the conversation

    Args:
        family: family of the command

    Returns:
        function used to handle the error
    """

    def fail(update: Update = None,
             context: CallbackContext = None,
             info: EventInfo = None,
             fail_file: str = "generic",
             return_value: int = None,
             **kwargs) -> int:
        """Handles an invalid message in the bid conversation.
        The filename is expected to be in the format of <family>\_error\_<fail\_file>.md.
        Returns a warning message

        Args:
            update: update event. Defaults to None
            context: context passed by the handler. Defaults to None
            event_info: if provided, overrides both update and context. Defaults to None
            fail_file: name of the markdown file that contains the fail message. Defaults to "generic"
            return_value: value of the next conversation state. Defaults to None (remains in the same state)
            kwargs: values passed to :func:`read_md`

        Returns:
            new state of the conversation
        """
        info = EventInfo.from_message(update, context) if not info else info
        text = read_md(f"{family}_error_{fail_file}", **kwargs)
        info.bot.send_message(chat_id=info.chat_id, text=text, parse_mode=ParseMode.MARKDOWN_V2)
        return return_value

    return fail


def conv_cancel(family: str) -> Callable:
    """Creates a function used to handle the /cancel command in the conversation

    Args:
        family: family of the command

    Returns:
        function used to handle the /cancel command
    """

    def cancel(update: Update, context: CallbackContext) -> int:
        """Handles the /cancel command.
        Exits the conversation

        Args:
            update: update event
            context: context passed by the handler

        Returns:
            new state of the conversation
        """
        info = EventInfo.from_message(update, context)
        text = read_md(f"{family}_cancel")
        info.bot.send_message(chat_id=info.chat_id, text=text, parse_mode=ParseMode.MARKDOWN_V2)
        return -1

    return cancel
