"""/sban command"""

from telegram import Update
from telegram.error import TelegramError
from telegram.ext import CallbackContext

from spotted.data import User
from spotted.utils import EventInfo, get_user_by_id_or_index


async def sban_cmd(update: Update, context: CallbackContext):
    """Handles the /sban command.
    Sban a user by using this command and listing all the user_id to sban

    Args:
        update: update event
        context: context passed by the handler
    """
    info = EventInfo.from_message(update, context)
    sban_fail = []
    if context.args is None or len(context.args) == 0:  # if no args have been passed
        banned_users = "\n".join(
            f"#{idx} ({user.ban_date:%d/%m/%Y %H:%M})" for idx, user in enumerate(User.banned_users())
        )
        banned_users = "Nessuno" if len(banned_users) == 0 else f"{banned_users}"
        text = (
            f"[uso]: /sban <user_id1|#idx> [...(user_id2|#idx)]\nGli utenti attualmente bannati sono:\n{banned_users}"
        )
        await info.bot.send_message(chat_id=info.chat_id, text=text)
        return

    num_sban = 0
    banned_users = User.banned_users()
    for user_id_or_idx in context.args:
        # Get the user to sban, either by user_id or by index in the banned users list
        user = get_user_by_id_or_index(user_id_or_idx, banned_users)
        if user is None:
            sban_fail.append(user_id_or_idx)
            continue

        user.sban()
        num_sban += 1
        try:
            await info.bot.send_message(
                chat_id=user.user_id, text="Sei stato sbannato da Spotted DMI, puoi tornare a postare!"
            )
        except TelegramError:  # We don't really care if the user cannot be notified by the bot
            pass
    errors = f"\nI seguenti sban sono falliti:\n{'\n'.join(sban_fail)}" if sban_fail else ""
    await info.bot.send_message(chat_id=info.chat_id, text=f"{num_sban} sban eseguiti con successo.{errors}")
