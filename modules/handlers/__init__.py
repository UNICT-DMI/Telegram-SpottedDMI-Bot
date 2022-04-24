"""Modules that handle the events the bot recognizes and reacts to"""
from datetime import time
import warnings
from pytz import utc
from telegram.ext import CallbackQueryHandler, CommandHandler, Dispatcher, Filters, MessageHandler
from modules.data.config import Config
from modules.debug import error_handler, log_message
from .anonym_comment import anonymous_comment_msg
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


def add_handlers(dp: Dispatcher):
    """Adds all the needed handlers to the dispatcher

    Args:
        dp (Dispatcher): supplyed dispatcher
    """
    warnings.filterwarnings("ignore",
                            message="If 'per_message=False', 'CallbackQueryHandler' will not be tracked for every message.")
    if Config.settings_get('debug', 'local_log'):  # add MessageHandler only if log_message is enabled
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

    if Config.meme_get('comments'):
        dp.add_handler(
            MessageHandler(Filters.forwarded & Filters.chat_type.groups & Filters.is_automatic_forward, forwarded_post_msg))
    if Config.meme_get('delete_anonymous_comments'):
        dp.add_handler(
            MessageHandler(Filters.sender_chat.channel & Filters.chat_type.groups & ~Filters.is_automatic_forward,
                           anonymous_comment_msg,
                           run_async=True))


def add_jobs(dp: Dispatcher):
    """Adds all the jobs to be scheduled to the dispatcher

    Args:
        dp (Dispatcher): supplyed dispatcher
    """
    dp.job_queue.run_daily(clean_pending_job, time=time(hour=5, tzinfo=utc))  # run each day at 05:00 utc
    dp.job_queue.run_daily(db_backup_job, time=time(hour=5, tzinfo=utc))  # run each day at 05:00 utc
