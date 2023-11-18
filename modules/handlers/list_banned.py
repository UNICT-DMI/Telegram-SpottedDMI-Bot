"""/list_banned command"""
from datetime import datetime
from telegram import Update
from telegram.ext import CallbackContext
from modules.data import DbManager
from modules.utils import EventInfo

def list_banned_cmd(update: Update, context: CallbackContext):
    info = EventInfo.from_message(update, context)
    users = DbManager.select_from(select="*", table_name="banned_users")
    info.bot.send_message(chat_id=info.chat_id, text=f"{write_banned_list(users)}",parse_mode='Markdown')

def write_banned_list(users: list)->str:
    text = "*La lista dei bannati:*\n\n"
    for user in users:
        date = get_human_readable_datetime(user["ban_date"])
        text += f"• {user['user_id']} bannato il {date}\n"
    return text

def get_human_readable_datetime(date:str)->str:
    datetime_object = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
    return datetime_object.strftime('%d/%m/%Y %H:%M')