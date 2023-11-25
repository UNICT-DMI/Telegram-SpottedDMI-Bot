"""/settings command"""
import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext

from spotted.data import User
from spotted.utils import EventInfo, get_settings_kb

logger = logging.getLogger(__name__)


async def settings_cmd(update: Update, context: CallbackContext):
    """Handles the /settings command.
    Let's the user choose whether his posts will be credited or not

    Args:
        update: update event
        context: context passed by the handler
    """
    info = EventInfo.from_message(update, context)
    await info.bot.send_message(
        chat_id=info.chat_id,
        text="***Come vuoi che sia il tuo post:***",
        reply_markup=get_settings_kb(),
        parse_mode=ParseMode.MARKDOWN_V2,
    )


async def settings_callback(update: Update, context: CallbackContext):
    """Handles the settings,[ anonimo | credit ] callback.

    - anonimo: Removes the user_id from the table of credited users, if present.
    - credit: Adds the user_id to the table of credited users, if it wasn't already there.

    Args:
        update: update event
        context: context passed by the handler
    """
    info = EventInfo.from_callback(update, context)
    user = User(info.user_id)
    action = info.args[0]

    if action == "anonimo":  # if the user wants to be anonym
        text = (
            "Sei già anonimo"
            if user.become_anonym()  # if the user was already anonym
            else "La tua preferenza è stata aggiornata\nOra i tuoi post saranno anonimi"
        )

    elif action == "credit":  # if the user wants to be credited
        text = "Sei già creditato nei post\n" if user.become_credited() else "La tua preferenza è stata aggiornata\n"
        text += (
            f"I tuoi post avranno come credit @{info.user_username}"
            if info.user_username
            else "ATTENZIONE:\nNon hai nessun username associato al tuo account telegram\n"
            "Se non lo aggiungi, non sarai creditato"
        )
    else:
        logger.error("settings_callback: invalid arg '%s'", action)
        return

    await info.bot.edit_message_text(chat_id=info.chat_id, message_id=info.message_id, text=text)
