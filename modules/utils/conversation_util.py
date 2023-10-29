"""Common functions needed in conversation handlers"""
from typing import Callable, Optional, Union
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext
from modules.data import read_md
from modules.utils.info_util import EventInfo


def conv_fail(
    family: str,
) -> Callable[[Union[tuple[Update, CallbackContext], EventInfo], str, Optional[int]], Optional[int]]:
    """Creates a function used to handle any error in the conversation

    Args:
        family: family of the command

    Returns:
        function used to handle the error
    """

    async def fail(
        event: Union[tuple[Update, CallbackContext], EventInfo],
        fail_file: str = "generic",
        return_value: Optional[int] = None,
        **kwargs,
    ) -> Optional[int]:
        """Handles an invalid message in the conversation.
        Optional[int]he filename is expected to be in the format of <family>_error_<fail_file>.md.
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
        info = event if isinstance(event, EventInfo) else EventInfo.from_message(*event)
        text = read_md(f"{family}_error_{fail_file}", **kwargs)
        await info.bot.send_message(chat_id=info.chat_id, text=text, parse_mode=ParseMode.MARKDOWN_V2)
        return return_value

    return fail


def conv_cancel(family: str) -> Callable[[Update, CallbackContext], int]:
    """Creates a function used to handle the /cancel command in the conversation.
    Invoking /cancel will exit the conversation immediately

    Args:
        family: family of the command

    Returns:
        function used to handle the /cancel command
    """

    async def cancel(update: Update, context: CallbackContext) -> int:
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
        await info.bot.send_message(chat_id=info.chat_id, text=text, parse_mode=ParseMode.MARKDOWN_V2)
        return -1

    return cancel
