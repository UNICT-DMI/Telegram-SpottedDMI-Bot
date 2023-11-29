"""Modules used in this bot"""
from telegram.ext import Application

from spotted.data import Config, init_db
from spotted.handlers import add_commands, add_handlers, add_jobs


def run_bot():
    """Init the database, add the handlers and start the bot"""

    init_db()
    application = Application.builder().token(Config.settings_get("token")).post_init(add_commands).build()
    add_handlers(application)
    add_jobs(application)

    application.run_polling()
