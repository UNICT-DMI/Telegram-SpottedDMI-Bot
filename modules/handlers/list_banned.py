"""/list_banned command"""
from datetime import datetime
from telegram import Update, ParseMode
from telegram.ext import CallbackContext
from modules.data import DbManager
from modules.utils import EventInfo

def list_banned_cmd(update: Update, context: CallbackContext):
    """The command to get a list of the current banned users
    with the user_id and date and time of the ban   

    Args:
        update (Update): update event
        context (CallbackContext): context passed by the handler
    """
    info = EventInfo.from_message(update, context)
    users = DbManager.select_from(select="*", table_name="banned_users")
    info.bot.send_message(chat_id=info.chat_id, text=f"{write_banned_list(users)}",parse_mode=ParseMode.MARKDOWN_V2)

def write_banned_list(users: list) -> str:
    """Write the list of banned users

    Args:
        users (list): a list of dictionaries containing query results

    Returns:
        str: the text of the message
    """
    text = "*La lista dei bannati:*\n"
    for user in users:
        datetime_object = datetime.strptime(user['ban_date'], '%Y-%m-%d %H:%M:%S')
        date = datetime_object.strftime('%d/%m/%Y %H:%M')
        text += f"• {user['user_id']} bannato il {date}\n"
    return text
