"""/ban command"""

from telegram import Update
from telegram.ext import CallbackContext

from spotted.data import PendingPost, Report, User
from spotted.utils import EventInfo


async def ban_cmd(update: Update, context: CallbackContext):
    """Handles the /ban command.
    Ban a user by replying to one of his pending posts with /ban

    Args:
        update: update event
        context: context passed by the handler
    """
    info = EventInfo.from_message(update, context)
    g_message_id = update.message.reply_to_message.message_id
    user_id = -1
    if (pending_post := PendingPost.from_group(admin_group_id=info.chat_id, g_message_id=g_message_id)) is not None:
        user_id = pending_post.user_id
        pending_post.delete_post()
        await info.edit_inline_keyboard(message_id=g_message_id)
    elif (report := Report.from_group(admin_group_id=info.chat_id, g_message_id=g_message_id)) is not None:
        user_id = report.user_id
    else:  # the reply does not refer to a pending post or a report
        await info.bot.send_message(
            chat_id=info.chat_id, text="Per bannare qualcuno, rispondi con /ban al suo post o report"
        )
        return

    user = User(user_id)
    if user.is_banned:
        await info.bot.send_message(chat_id=info.chat_id, text="L'utente è già bannato")
        return
    user.ban()
    await info.bot.send_message(chat_id=info.chat_id, text="L'utente è stato bannato")
    await info.bot.send_message(
        chat_id=user.user_id,
        text="Grazie per il tuo contributo alla community, a causa "
        "di un tuo comportamento inadeguato sei stato bannato da Spotted DMI. Alla prossima!",
    )
