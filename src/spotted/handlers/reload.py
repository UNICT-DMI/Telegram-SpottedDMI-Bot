"""/reload command"""
from telegram import Update
from telegram.ext import CallbackContext

from spotted.data import Config
from spotted.utils import EventInfo


async def reload_cmd(update: Update, context: CallbackContext):
    """Handles the /reload command.
    Reload the configuration file, updating the bot's settings.
    This incudes both the _settings.yaml_ and the _autorereply.yaml_ file.
    This way the bot can be updated without restarting it.

    In actuality, the current singleton is destroyed and a new one is created
    as soon as a configuration request is deemed necessary.

    Args:
        update: update event
        context: context passed by the handler

    Warning:
        Loading different configurations may cause inconsistencies in live conversations.
    """
    info = EventInfo.from_message(update, context)
    Config.reload()
    await info.bot.send_message(
        chat_id=info.chat_id, text="Configurazione ricaricata", reply_to_message_id=info.message_id
    )
