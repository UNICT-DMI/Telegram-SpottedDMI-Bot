"""/unmute command"""

from telegram import Update
from telegram.error import TelegramError
from telegram.ext import CallbackContext

from spotted.data import User
from spotted.utils import EventInfo, get_user_by_id_or_index


async def unmute_cmd(update: Update, context: CallbackContext):
    """Handles the /unmute command.
    Unmute a user by using this command and listing all the user_id to unmute

    Args:
        update: update event
        context: context passed by the handler
    """
    info = EventInfo.from_message(update, context)
    failed_unmute = []
    if context.args is None or len(context.args) == 0:  # if no args have been passed
        if len(User.muted_users()) == 0:
            muted_users = "Nessuno"
        else:
            muted_users = "\n".join(
                f"#{i} (Mute: {user.mute_date:%d/%m/%Y %H:%M} - Exp: {user.mute_expire_date:%d/%m/%Y %H:%M} )"
                for i, user in enumerate(User.muted_users())
            )
        text = (
            f"[uso]: /unmute <user_id1|#idx> [...(user_id2|#idx)]\nGli utenti attualmente mutati sono:\n{muted_users}"
        )
        await info.bot.send_message(chat_id=info.chat_id, text=text)
        return

    num_unmuted = 0
    muted_users = User.muted_users()
    for user_id_or_idx in context.args:
        # Get the user to unmute, either by user_id or by index in the muted users list
        user = get_user_by_id_or_index(user_id_or_idx, muted_users)
        if user is None:
            failed_unmute.append(user_id_or_idx)
            continue

        await user.unmute(info.bot)
        num_unmuted += 1
        try:
            await info.bot.send_message(
                chat_id=user.user_id, text="Sei stato smutato da Spotted DMI, puoi tornare a commentare!"
            )
        except TelegramError:  # We don't really care if the user cannot be notified by the bot
            pass
    errors = "\nI seguenti unmute sono falliti:\n" + "\n".join(failed_unmute) if len(failed_unmute) > 0 else ""
    await info.bot.send_message(chat_id=info.chat_id, text=f"{num_unmuted} unmute eseguiti con successo.{errors}")
