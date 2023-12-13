"""/sban command"""
from telegram import Update
from telegram.error import Forbidden
from telegram.ext import CallbackContext

from spotted.data import User
from spotted.utils import EventInfo


async def sban_cmd(update: Update, context: CallbackContext):
    """Handles the /sban command.
    Sban a user by using this command and listing all the user_id to sban

    Args:
        update: update event
        context: context passed by the handler
    """
    info = EventInfo.from_message(update, context)
    sban_fail = False
    if context.args is None or len(context.args) == 0:  # if no args have been passed
        banned_users = "\n".join(f"{user.user_id} ({user.ban_date:%d/%m/%Y %H:%M})" for user in User.banned_users())
        banned_users = "Nessuno" if len(banned_users) == 0 else f"{banned_users}"
        text = f"[uso]: /sban <user_id1> [...user_id2]\nGli utenti attualmente bannati sono:\n{banned_users}"
        await info.bot.send_message(chat_id=info.chat_id, text=text)
        return
    for user_id in context.args:
        if User(int(user_id)).sban():
            try:
                await info.bot.send_message(
                    chat_id=user_id, text="Sei stato sbannato da Spotted DMI, puoi tornare a postare!"
                )
            except Forbidden:
                pass
        else:
            # the sban was unsuccessful (maybe the user id was not found)
            sban_fail = True
            continue
    reply_text = "Sban effettuato" if not sban_fail else "Uno o più sban sono falliti"
    await info.bot.send_message(chat_id=info.chat_id, text=reply_text)
