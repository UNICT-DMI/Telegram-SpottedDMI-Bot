"""Main module"""
# region imports
# libs
import warnings
from datetime import time
from pytz import utc
# telegram
from telegram import BotCommand
from telegram.ext import CallbackQueryHandler, CommandHandler, Dispatcher, Filters, MessageHandler, Updater
# data
from modules.data import config_map
# debug
from modules.debug import error_handler, log_message
# handlers
from modules.handlers import (ban_cmd, cancel_cmd, clean_pending_cmd, clean_pending_job, db_backup_cmd, db_backup_job, forwarded_post_msg, help_cmd,
                              purge_cmd, reply_cmd, rules_cmd, sban_cmd, settings_cmd, spot_conv_handler, start_cmd,
                              stats_callback, stats_cmd, report_user_conv_handler, report_spot_conv_handler)
from modules.handlers.callback_handlers import meme_callback

# endregion


def add_commands(up: Updater):
    """Adds the list of commands with their description to the bot

    Args:
        up (Updater): supplyed Updater
    """
    commands = [
        BotCommand("start", "presentazione iniziale del bot"),
        BotCommand("spot", "inizia a spottare"),
        BotCommand("cancel ",
                   "annulla la procedura in corso e cancella l'ultimo spot inviato, se non è ancora stato pubblicato"),
        BotCommand("help ", "funzionamento e scopo del bot"),
        BotCommand("report", "segnala un utente"),
        BotCommand("rules ", "regole da tenere a mente"),
        BotCommand("stats", "visualizza statistiche sugli spot"),
        BotCommand("settings", "cambia le impostazioni di privacy")
    ]
    up.bot.set_my_commands(commands=commands)


def add_handlers(dp: Dispatcher):
    """Adds all the needed handlers to the dispatcher

    Args:
        dp (Dispatcher): supplyed dispatcher
    """
    if config_map['debug']['local_log']:  # add MessageHandler only if log_message is enabled
        dp.add_handler(MessageHandler(Filters.all, log_message), 1)

    # Error handler
    dp.add_error_handler(error_handler)

    # Conversation handler
    dp.add_handler(spot_conv_handler())

    dp.add_handler(report_user_conv_handler())

    dp.add_handler(report_spot_conv_handler())
    # Command handlers
    dp.add_handler(CommandHandler("start", start_cmd))
    dp.add_handler(CommandHandler("help", help_cmd))
    dp.add_handler(CommandHandler("rules", rules_cmd))
    dp.add_handler(CommandHandler("stats", stats_cmd))
    dp.add_handler(CommandHandler("settings", settings_cmd))
    dp.add_handler(CommandHandler("sban", sban_cmd))
    dp.add_handler(CommandHandler("clean_pending", clean_pending_cmd))
    dp.add_handler(CommandHandler("db_backup", db_backup_cmd, run_async=True))
    dp.add_handler(CommandHandler("purge", purge_cmd, run_async=True))
    dp.add_handler(CommandHandler("cancel", cancel_cmd))  # it must be after the conversation handler's 'cancel'

    # MessageHandler
    dp.add_handler(MessageHandler(Filters.reply & Filters.regex(r"^/ban$"), ban_cmd))
    dp.add_handler(MessageHandler(Filters.reply & Filters.regex(r"^/reply"), reply_cmd))

    # Callback handlers
    dp.add_handler(CallbackQueryHandler(meme_callback, pattern=r"^meme_\.*"))
    dp.add_handler(CallbackQueryHandler(stats_callback, pattern=r"^stats_\.*"))

    if config_map['meme']['comments']:
        dp.add_handler(MessageHandler(Filters.forwarded, forwarded_post_msg))


def add_jobs(dp: Dispatcher):
    """Adds all the jobs to be scheduled to the dispatcher

    Args:
        dp (Dispatcher): supplyed dispatcher
    """
    dp.job_queue.run_daily(clean_pending_job, time=time(hour=5, tzinfo=utc))  # run each day at 05:00 utc
    dp.job_queue.run_daily(db_backup_job, time=time(hour=5, tzinfo=utc))  # run each day at 05:00 utc


def main():
    """Main function
    """
    updater = Updater(config_map['token'], request_kwargs={'read_timeout': 20, 'connect_timeout': 20}, use_context=True)
    add_commands(updater)
    add_handlers(updater.dispatcher)
    add_jobs(updater.dispatcher)

    updater.start_polling()
    updater.idle()


warnings.filterwarnings("ignore",
                        message="If 'per_message=False', 'CallbackQueryHandler' will not be tracked for every message.")
if __name__ == "__main__":
    main()
