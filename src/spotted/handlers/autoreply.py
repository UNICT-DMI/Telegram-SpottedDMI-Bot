"""/autoreply command"""
from telegram import Update
from telegram.ext import CallbackContext

from spotted.data import Config, PendingPost, Report
from spotted.utils import EventInfo

from .approve import reject_post


async def autoreply_cmd(update: Update, context: CallbackContext):
    """Handles the /autoreply command.
    Used by replying to one of his pending posts with /autoreply + one of the keys
    in the autoreplies dictionary in the config file.
    Send a message to the user with the autoreply message to inform them about a problem with their post

    Args:
        update: update event
        context: context passed by the handler
    """
    info = EventInfo.from_message(update, context)

    arg = " ".join(info.args)
    print("ARGS:", arg)
    if arg not in Config.autoreplies_get("autoreplies") or arg == "lista":
        possible_args_text = "\n - ".join(Config.autoreplies_get("autoreplies").keys())
        text = f"Possibili argomenti:\n - {possible_args_text}"
        await info.bot.send_message(chat_id=info.chat_id, text=text)
        return

    g_message_id = update.message.reply_to_message.message_id
    if (pending_post := PendingPost.from_group(admin_group_id=info.chat_id, g_message_id=g_message_id)) is not None:
        user_id = pending_post.user_id
    elif (report := Report.from_group(admin_group_id=info.chat_id, g_message_id=g_message_id)) is not None:
        user_id = report.user_id
    else:  # the message was not a pending post or a report
        await info.bot.send_message(
            chat_id=info.chat_id,
            text="Il messaggio selezionato non è valido.\n"
            "Per mandare un messaggio ad un utente, rispondere al suo post o report con /autoreply",
        )
        return

    text = Config.autoreplies_get("autoreplies")[arg]
    await info.bot.send_message(chat_id=user_id, text=f"COMUNICAZIONE DEGLI ADMIN SUL TUO ULTIMO POST:\n{text}")
    await info.bot.send_message(
        chat_id=info.chat_id, text="L'utente ha ricevuto il messaggio", reply_to_message_id=g_message_id
    )


async def autoreply_callback(update: Update, context: CallbackContext):
    """Handles the autoreply callback.
    Reply to the user with the autoreply message to inform them about the reason of the rejection

    Args:
        update: update event
        context: context passed by the handler
    """
    info = EventInfo.from_callback(update, context)
    arg = info.args[0]  # arg is the key of the autoreplies dictionary in the config file

    all_autoreplies = Config.autoreplies_get("autoreplies")
    current_reply = all_autoreplies.get(arg)
    pending_post = PendingPost.from_group(admin_group_id=info.chat_id, g_message_id=info.message_id)

    if pending_post:
        await info.bot.send_message(chat_id=pending_post.user_id, text=current_reply)

        if Config.settings_get("post", "reject_after_autoreply"):
            await reject_post(info=info, pending_post=pending_post, reason=arg)

    return None
