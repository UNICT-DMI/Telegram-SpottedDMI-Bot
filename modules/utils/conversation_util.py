# pylint: disable=anomalous-backslash-in-string
"""Common functions needed in conversation handlers"""
from typing import Callable, Optional
from telegram import Update, ParseMode
from telegram.ext import CallbackContext
from modules.data import read_md
from modules.utils.info_util import EventInfo


def conv_fail(
    family: str
) -> Callable[[Optional[Update], Optional[CallbackContext], Optional[EventInfo], Optional[str], Optional[int]], int]:
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
        """Handles an invalid message in the conversation.
        The filename is expected to be in the format of <family>_error_<fail_file>.md.
        Returns a warning message

        Args:
            update: update event
            context: context passed by the handler
            event_info: if provided, overrides both update and context
            fail_file: name of the markdown file that contains the fail message
            return_value: value of the next conversation state. If default, remains in the same state.
            kwargs: values passed to :func:`read_md`

        Returns:
            new state of the conversation
        """
        info = EventInfo.from_message(update, context) if not info else info
        text = read_md(f"{family}_error_{fail_file}", **kwargs)
        info.bot.send_message(chat_id=info.chat_id, text=text, parse_mode=ParseMode.MARKDOWN_V2)
        return return_value

    return fail


def conv_cancel(family: str) -> Callable[[Update, CallbackContext], int]:
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
