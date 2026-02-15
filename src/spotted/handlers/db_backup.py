"""/db_backup command"""

from telegram import Update
from telegram.ext import CallbackContext

from spotted.data import Config
from spotted.utils import EventInfo

from .job_handlers import db_backup_job


async def db_backup_cmd(update: Update, context: CallbackContext):
    """Handles the /db_backup command.
    Automatically upload and send current version of db for backup

    Args:
        _: update event
        context: context passed by the handler
    """
    if Config.debug_get("backup_chat_id") == 0:
        info = EventInfo.from_message(update, context)
        await info.bot.send_message(
            chat_id=info.chat_id,
            reply_to_message_id=info.message_id,
            text="La funzionalità di backup è disabilitata. Imposta `backup_chat_id` per abilitarla.",
        )
        return
    await db_backup_job(context=context)
