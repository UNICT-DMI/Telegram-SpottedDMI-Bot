"""/unmute command"""

from telegram import Update
from telegram.error import Forbidden
from telegram.ext import CallbackContext

from spotted.data import User
from spotted.utils import EventInfo


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
        muted_users = "\n".join(
            f"{user.user_id} (Mute: {user.mute_date:%d/%m/%Y %H:%M} - Exp: {user.mute_expire_date:%d/%m/%Y %H:%M} )"
            for user in User.muted_users()
        )
        muted_users = "Nessuno" if len(muted_users) == 0 else f"{muted_users}"
        text = f"[uso]: /unmute <user_id1> [...user_id2]\nGli utenti attualmente mutati sono:\n{muted_users}"
        await info.bot.send_message(chat_id=info.chat_id, text=text)
        return
    for user_id in context.args:
        try:
            await User(int(user_id)).unmute(info.bot)
            await info.bot.send_message(
                chat_id=user_id, text="Sei stato smutato da Spotted DMI, puoi tornare a commentare!"
            )
        except Forbidden:
            pass
        except ValueError:
            failed_unmute.append(user_id)
    text = "senza errori" if not failed_unmute else "con errori per i seguenti utenti:\n" + ",".join(failed_unmute)
    await info.bot.send_message(chat_id=info.chat_id, text="Unmute eseguito " + text)
