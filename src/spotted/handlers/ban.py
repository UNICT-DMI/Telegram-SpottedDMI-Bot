"""/ban command"""

from telegram import Update
from telegram.ext import CallbackContext

from spotted.data import Config, PendingPost, Report, User
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
    await execute_ban(user_id, info)


async def execute_ban(user_id: int, info: EventInfo, from_warn: bool = False):
    """Execute the ban of a user by his user_id

    Args:
        user_id: The user_id of the user to ban
        info: The EventInfo object
        from_warn: A boolean indicating if the ban is executed from a warn
    """
    user = User(user_id)
    receipt_chat_id = info.chat_id if not from_warn else Config.post_get("admin_group_id")
    if user.is_banned:
        await info.bot.send_message(chat_id=receipt_chat_id, text=f"L'utente {user_id} è già bannato")
        return
    user.ban()
    await info.bot.send_message(chat_id=receipt_chat_id, text=f"L'utente {user_id} è stato bannato")
    await info.bot.send_message(
        chat_id=user.user_id,
        text="Grazie per il tuo contributo alla community, a causa "
        "di un tuo comportamento inadeguato sei stato bannato da Spotted DMI. Alla prossima!",
    )
