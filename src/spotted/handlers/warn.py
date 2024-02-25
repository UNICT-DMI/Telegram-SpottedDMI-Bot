"""/warn command"""
from telegram import Update
from telegram.ext import CallbackContext

from spotted.data import Config, PendingPost, Report, User
from spotted.handlers.ban import execute_ban
from spotted.utils import EventInfo


async def warn_cmd(update: Update, context: CallbackContext):
    """Handles the /warn command.
     Warn a user by replying to a user'comment on the community group or to a pending spot/report.
    Args:
        update: update event
        context: context passed by the handler
    """
    info = EventInfo.from_message(update, context)
    admins = [admin.user.id for admin in await info.bot.get_chat_administrators(Config.post_get("community_group_id"))]
    g_message = update.message.reply_to_message
    if info.user_id not in admins:
        await info.bot.send_message(chat_id=info.user_id, text="Non sei admin")
        await info.message.delete()
        return
    if (g_message is None) or len(context.args) == 0:
        text = "Per warnare rispondi ad un commento/report/pending post con\n/warn <motivo>"
        await info.bot.send_message(chat_id=Config.post_get("admin_group_id"), text=text)
        await info.message.delete()
        return
    comment = " ".join(context.args)
    from_community = False
    user_id = -1
    if (
        pending_post := PendingPost.from_group(admin_group_id=info.chat_id, g_message_id=g_message.message_id)
    ) is not None:
        user_id = pending_post.user_id
        pending_post.delete_post()
        await info.edit_inline_keyboard(message_id=g_message.message_id)
    elif (report := Report.from_group(admin_group_id=info.chat_id, g_message_id=g_message.message_id)) is not None:
        user_id = report.user_id
    elif g_message.chat_id == Config.post_get("community_group_id"):
        user_id = g_message.from_user.id
        from_community = True
    else:
        return
    await execute_warn(info, user_id, comment, from_community)


async def execute_warn(info: EventInfo, user_id: int, comment: str, from_community: bool = False):
    """Execute the /warn command.
    Add a warn to the user and auto-ban is necessary
     Args:
         user_id: The user_id of the interested user
         bot: a telegram bot instance
         from_community: a flag for auto-delete command invokation
    """
    user = User(user_id)
    user.warn()
    n_warns = user.get_n_warns()
    await info.bot.send_message(
        chat_id=user.user_id,
        text=f"Sei stato warnato su SpottedDMI, hai {n_warns} warn su"
        f" un massimo di {Config.post_get('max_n_warns')} in "
        f"{Config.post_get('warn_expiration_days')} giorni!\n"
        f"Raggiunto il massimo sarai bannato!\n\n\n"
        f"Motivo: {comment}",
    )
    await info.bot.send_message(
        chat_id=Config.post_get("admin_group_id"),
        text=f"L'utente {user_id} ha ricevuto il {n_warns}° warn\n" f"Motivo: {comment}",
    )
    if user.is_warn_bannable:
        await execute_ban(user.user_id, info)
    if from_community:
        await info.message.delete()
