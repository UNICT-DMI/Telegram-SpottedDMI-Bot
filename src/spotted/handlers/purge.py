"""/purge command"""
from time import sleep

from telegram import Update
from telegram.ext import CallbackContext

from spotted.data import DbManager
from spotted.utils import EventInfo

purge_in_progress = False  # pylint: disable=invalid-name


async def purge_cmd(update: Update, context: CallbackContext):
    """Handles the /purge command.
    Deletes all posts and the related votes in the database whose actual telegram message could not be found

    Args:
        update: update event
        context: context passed by the handler
    """
    global purge_in_progress  # pylint: disable=global-statement,invalid-name
    info = EventInfo.from_message(update, context)
    if not purge_in_progress:  # there is no purge already in progress
        purge_in_progress = True
        await info.bot.send_message(info.chat_id, text="Avvio del comando /purge")
        published_posts = DbManager.select_from("published_post")
        total_posts = len(published_posts)
        lost_posts = 0
        for published_post in published_posts:
            try:
                message = await info.bot.forward_message(
                    info.chat_id,
                    from_chat_id=published_post["channel_id"],
                    message_id=published_post["c_message_id"],
                    disable_notification=True,
                )
                message.delete()
            except Exception:  # pylint: disable=broad-except
                lost_posts += 1
                sleep(10)
            finally:
                sleep(0.2)

        avg = round(lost_posts / (total_posts if total_posts != 0 else 1), 3)
        await info.bot.send_message(
            info.chat_id, text=f"Dei {total_posts} totali, {lost_posts} sono andati persi. Il rapporto è {avg}"
        )
        purge_in_progress = False
