"""/db_backup command"""
from telegram import Update
from telegram.ext import CallbackContext
from modules.handlers.job_handlers import db_backup_job
from modules.data import config_map
from modules.utils import EventInfo


def db_backup_cmd(update: Update, context: CallbackContext):
    """Handles the /db_backup command.
    Automatically upload and send current version of db for backup

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler
    """
    info = EventInfo.from_message(update, context)
    if info.chat_id == config_map['meme']['group_id']:  # you have to be in the admin group
        db_backup_job(context=context)
