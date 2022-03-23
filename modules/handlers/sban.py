"""/sban command"""
from telegram import Update
from telegram.ext import CallbackContext
from modules.data import Config, User
from modules.utils import EventInfo


def sban_cmd(update: Update, context: CallbackContext):
    """Handles the /sban command.
    Sban a user by using this command and listing all the user_id to sban

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler
    """
    info = EventInfo.from_message(update, context)
    if info.chat_id == Config.meme_get('group_id'):  # you have to be in the admin group
        if len(context.args) == 0:  # if no args have been passed
            info.bot.send_message(chat_id=info.chat_id, text="[uso]: /sban <user_id1> [...user_id2]")
            return
        for user_id in context.args:
            # the sban was unsuccesful (maybe the user id was not found)
            if not User(user_id).sban():
                break
        else:
            info.bot.send_message(chat_id=info.chat_id, text="Sban effettuato")
            return
        info.bot.send_message(chat_id=info.chat_id, text="Uno o più sban sono falliti")
