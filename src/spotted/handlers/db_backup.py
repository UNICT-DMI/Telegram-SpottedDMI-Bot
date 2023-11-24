"""/db_backup command"""
from telegram import Update
from telegram.ext import CallbackContext

from .job_handlers import db_backup_job


async def db_backup_cmd(_: Update, context: CallbackContext):
    """Handles the /db_backup command.
    Automatically upload and send current version of db for backup

    Args:
        _: update event
        context: context passed by the handler
    """
    await db_backup_job(context=context)
