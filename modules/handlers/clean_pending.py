"""/clean_pending command"""
from telegram import Update
from telegram.ext import CallbackContext
from modules.handlers.job_handlers import clean_pending_job


def clean_pending_cmd(_: Update, context: CallbackContext):
    """Handles the /clean_pending command.
    Automatically rejects all pending posts that are older than the chosen amount of hours

    Args:
        _: update event
        context: context passed by the handler
    """
    clean_pending_job(context=context)
