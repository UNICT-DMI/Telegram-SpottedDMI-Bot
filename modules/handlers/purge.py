"""/purge command"""
from time import sleep
from telegram import Update
from telegram.ext import CallbackContext
from modules.data import config_map, DbManager
from modules.utils import EventInfo

purge_in_progress = False

def purge_cmd(update: Update, context: CallbackContext):
    """Handles the /purge command.
    Deletes all posts and the related votes in the database whose actual telegram message could not be found

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler
    """
    global purge_in_progress
    info = EventInfo.from_message(update, context)
    if info.chat_id == config_map['meme']['group_id'] and not purge_in_progress:  # you have to be in the admin group
        purge_in_progress = True
        info.bot.send_message(info.chat_id, text="Avvio del comando /purge")
        published_memes = DbManager.select_from("published_meme")
        total_posts = len(published_memes)
        lost_posts = 0
        for published_meme in published_memes:
            try:
                message = info.bot.forward_message(info.chat_id,
                                                   from_chat_id=published_meme['channel_id'],
                                                   message_id=published_meme['c_message_id'],
                                                   disable_notification=True)
                message.delete()
            except Exception as e:
                lost_posts += 1
                sleep(10)
            finally:
                sleep(0.2)
        info.bot.send_message(
            info.chat_id,
            text=
            f"Dei {total_posts} totali, {lost_posts} sono andati persi. Il rapporto è {round(lost_posts/total_posts, 3)}")
        purge_in_progress = False
