"""/clean_pending command"""
from telegram import Update
from telegram.ext import CallbackContext
from modules.handlers.job_handlers import clean_pending_job
from modules.data import config_map
from modules.utils import EventInfo


def clean_pending_cmd(update: Update, context: CallbackContext):
    """Handles the /clean_pending command.
    Automatically rejects all pending posts that are older than the chosen amount of hours

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler
    """
    info = EventInfo.from_message(update, context)
    if info.chat_id == config_map['meme']['group_id']:  # you have to be in the admin group
        clean_pending_job(context=context)
