"""Scheduled jobs of the bot"""
from datetime import datetime, timezone, timedelta
from telegram.ext import CallbackContext
from telegram.error import BadRequest, Unauthorized
from modules.debug.log_manager import logger
from modules.data.data_reader import config_map
from modules.data.meme_data import MemeData
from modules.utils.info_util import get_job_info


def clean_pending_job(context: CallbackContext):
    """Job called each day at 05:00 utc.
    Automatically rejects all pending posts that are older than the chosen amount of hours

    Args:
        context (CallbackContext): context passed by the jobqueue
    """
    info = get_job_info(context)
    admin_group_id = config_map['meme']['group_id']

    before_time = datetime.now(tz=timezone.utc) - timedelta(hours=config_map['meme']['remove_after_h'])
    pending_meme_ids = MemeData.get_list_pending_memes(group_id=admin_group_id, before=before_time)

    # For each pending meme older than before_time
    removed = 0
    for meme_id in pending_meme_ids:
        try:  # deleting the message associated with the pending meme to remote
            info['bot'].delete_message(chat_id=admin_group_id, message_id=meme_id)
            removed += 1
            try:  # sending a notification to the user
                user_id = MemeData.get_user_id(group_id=admin_group_id, g_message_id=meme_id)
                info['bot'].send_message(
                    chat_id=user_id,
                    text="Gli admin erano sicuramente molto impegnati e non sono riusciti a valutare lo spot in tempo")
            except (BadRequest, Unauthorized) as e:
                logger.warning("Notifying the user on /clean_pending: %s", e)
        except BadRequest as e:
            logger.error("Deleting old pending message: %s", e)
        finally:  # delete the data associated with the pending meme
            MemeData.remove_pending_meme(group_id=admin_group_id, g_message_id=meme_id)

    info['bot'].send_message(chat_id=admin_group_id, text=f"Sono stati eliminati {removed} messaggi rimasti in sospeso")
