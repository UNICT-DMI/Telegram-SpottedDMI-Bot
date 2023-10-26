"""Modules that handle the events the bot recognizes and reacts to"""
from datetime import time
import warnings
from pytz import utc
from telegram import BotCommand
from telegram.ext import CallbackQueryHandler, CommandHandler, Dispatcher, Filters, MessageHandler, Updater
from modules.data.config import Config
from modules.debug import error_handler, log_message
from .anonym_comment import anonymous_comment_msg
from .autoreply import autoreply_cmd
from .ban import ban_cmd
from .callback_handlers import meme_callback
from .cancel import cancel_cmd
from .clean_pending import clean_pending_cmd
from .db_backup import db_backup_cmd
from .forwarded_post import forwarded_post_msg
from .help import help_cmd
from .job_handlers import clean_pending_job, db_backup_job
from .purge import purge_cmd
from .reply import reply_cmd
from .report_spot import report_spot_conv_handler
from .report_user import report_user_conv_handler
from .rules import rules_cmd
from .sban import sban_cmd
from .settings import settings_cmd
from .spot import spot_conv_handler
from .start import start_cmd
from .stats import stats_callback, stats_cmd
from .follow_spot import follow_spot_callback
from .follow_comment import follow_spot_comment


def add_commands(updater: Updater):
    """Adds the list of commands with their description to the bot

    Args:
        updater: supplied Updater
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
    updater.bot.set_my_commands(commands=commands)


def add_handlers(disp: Dispatcher):
    """Adds all the needed handlers to the dispatcher

    Args:
        disp: supplied dispatcher
    """
    warnings.filterwarnings("ignore",
                            message="If 'per_message=False', 'CallbackQueryHandler' will not be tracked for every message.")

    if Config.settings_get('debug', 'local_log'):  # add MessageHandler only if log_message is enabled
        disp.add_handler(MessageHandler(Filters.all, log_message), 1)

    admin_filter = Filters.chat(chat_id=Config.meme_get('group_id'))

    # Error handler
    disp.add_error_handler(error_handler)

    # Conversation handler
    disp.add_handler(spot_conv_handler())
    disp.add_handler(report_user_conv_handler())
    disp.add_handler(report_spot_conv_handler())

    # Command handlers
    disp.add_handler(CommandHandler("start", start_cmd))
    disp.add_handler(CommandHandler("help", help_cmd))
    disp.add_handler(CommandHandler("rules", rules_cmd))
    disp.add_handler(CommandHandler("stats", stats_cmd))
    disp.add_handler(CommandHandler("settings", settings_cmd))
    disp.add_handler(CommandHandler("sban", sban_cmd, filters=admin_filter))
    disp.add_handler(CommandHandler("clean_pending", clean_pending_cmd, filters=admin_filter))
    disp.add_handler(CommandHandler("db_backup", db_backup_cmd, run_async=True, filters=admin_filter))
    disp.add_handler(CommandHandler("purge", purge_cmd, run_async=True, filters=admin_filter))
    disp.add_handler(CommandHandler("cancel", cancel_cmd))  # it must be after the conversation handler's 'cancel'

    # MessageHandler
    disp.add_handler(MessageHandler(Filters.reply & admin_filter & Filters.regex(r"^/ban$"), ban_cmd))
    disp.add_handler(MessageHandler(Filters.reply & admin_filter & Filters.regex(r"^/reply"), reply_cmd))
    disp.add_handler(MessageHandler(Filters.reply & admin_filter & Filters.regex(r"^/autoreply"), autoreply_cmd))
    disp.add_handler(MessageHandler(Filters.reply & Filters.chat_type.groups, follow_spot_comment, run_async=True))

    # Callback handlers
    disp.add_handler(CallbackQueryHandler(meme_callback, pattern=r"^meme_\.*"))
    disp.add_handler(CallbackQueryHandler(stats_callback, pattern=r"^stats_\.*"))
    disp.add_handler(CallbackQueryHandler(follow_spot_callback, pattern=r"^follow_\.*"))

    if Config.meme_get('comments'):
        disp.add_handler(
            MessageHandler(Filters.forwarded & Filters.chat_type.groups & Filters.is_automatic_forward, forwarded_post_msg))
    if Config.meme_get('delete_anonymous_comments'):
        disp.add_handler(
            MessageHandler(Filters.sender_chat.channel & Filters.chat_type.groups & ~Filters.is_automatic_forward,
                           anonymous_comment_msg,
                           run_async=True))


def add_jobs(disp: Dispatcher):
    """Adds all the jobs to be scheduled to the dispatcher

    Args:
        disp: supplyed dispatcher
    """
    disp.job_queue.run_daily(clean_pending_job, time=time(hour=5, tzinfo=utc))  # run each day at 05:00 utc
    disp.job_queue.run_daily(db_backup_job, time=time(hour=5, tzinfo=utc))  # run each day at 05:00 utc
