"""Modules that handle the events the bot recognizes and reacts to"""
from datetime import time
from warnings import filterwarnings

from pytz import utc
from telegram import BotCommand, BotCommandScopeAllPrivateChats, BotCommandScopeChat
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)
from telegram.warnings import PTBUserWarning

from spotted.data.config import Config
from spotted.debug import error_handler, log_message

from .anonym_comment import anonymous_comment_msg
from .approve import approve_no_callback, approve_status_callback, approve_yes_callback
from .autoreply import autoreply_callback, autoreply_cmd
from .ban import ban_cmd
from .cancel import cancel_cmd
from .clean_pending import clean_pending_cmd
from .db_backup import db_backup_cmd
from .follow_comment import follow_spot_comment
from .follow_spot import follow_spot_callback
from .forwarded_post import forwarded_post_msg
from .help import help_cmd
from .job_handlers import clean_pending_job, db_backup_job
from .purge import purge_cmd
from .reload import reload_cmd
from .reply import reply_cmd
from .report_spot import report_spot_conv_handler
from .report_user import report_user_conv_handler
from .rules import rules_cmd
from .sban import sban_cmd
from .settings import settings_callback, settings_cmd
from .spot import spot_conv_handler
from .start import start_cmd


async def add_commands(app: Application):
    """Adds the list of commands with their description to the bot

    Args:
        app: supplied application
    """
    private_chat_commands = [
        BotCommand("start", "presentazione iniziale del bot"),
        BotCommand("spot", "inizia a spottare"),
        BotCommand(
            "cancel ",
            "annulla la procedura in corso e cancella l'ultimo spot inviato, se non è ancora stato pubblicato",
        ),
        BotCommand("help ", "funzionamento e scopo del bot"),
        BotCommand("report", "segnala un utente"),
        BotCommand("rules ", "regole da tenere a mente"),
        BotCommand("settings", "cambia le impostazioni di privacy"),
    ]
    admin_commands = [
        BotCommand("ban", "banna un utente"),
        BotCommand("sban", "banna un utente"),
        BotCommand("reply", "rispondi ad uno spot o un report"),
        BotCommand("autoreply", "rispondi ad uno spot o un report con un messaggio automatico"),
        BotCommand("reload", "ricarica la configurazione del bot"),
        BotCommand("db_backup", "esegui il backup del database"),
        BotCommand("clean_pending", "elimina tutti gli spot in sospeso"),
    ]
    await app.bot.set_my_commands(private_chat_commands, scope=BotCommandScopeAllPrivateChats())
    await app.bot.set_my_commands(admin_commands, scope=BotCommandScopeChat(Config.post_get("admin_group_id")))


def add_handlers(app: Application):
    """Adds all the needed handlers to the application

    Args:
        app: supplied application
    """
    # Ignore the 'per_message' warning of the CallbackQueryHandler, since it's not a problem
    # https://github.com/python-telegram-bot/python-telegram-bot/wiki/Frequently-Asked-Questions#what-do-the-per_-settings-in-conversationhandler-do
    filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)

    if Config.settings_get("debug", "local_log"):  # add MessageHandler only if log_message is enabled
        app.add_handler(MessageHandler(filters.ALL, log_message), 1)

    admin_filter = filters.Chat(chat_id=Config.post_get("admin_group_id"))
    community_filter = filters.Chat(chat_id=Config.post_get("community_group_id"))

    # Error handler
    app.add_error_handler(error_handler)

    # Conversation handler
    app.add_handler(spot_conv_handler())
    app.add_handler(report_user_conv_handler())
    app.add_handler(report_spot_conv_handler())

    # Command handlers
    app.add_handler(CommandHandler("start", start_cmd, filters=filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("help", help_cmd, filters=filters.ChatType.PRIVATE | admin_filter))
    app.add_handler(CommandHandler("rules", rules_cmd, filters=filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("settings", settings_cmd, filters=filters.ChatType.PRIVATE))
    # it must be after the conversation handler's 'cancel'
    app.add_handler(CommandHandler("cancel", cancel_cmd, filters=filters.ChatType.PRIVATE))

    # Command handlers: Admin commands
    app.add_handler(CommandHandler("sban", sban_cmd, filters=admin_filter))
    app.add_handler(CommandHandler("clean_pending", clean_pending_cmd, filters=admin_filter))
    app.add_handler(CommandHandler("db_backup", db_backup_cmd, filters=admin_filter))
    app.add_handler(CommandHandler("purge", purge_cmd, filters=admin_filter))
    app.add_handler(CommandHandler("reload", reload_cmd, filters=admin_filter))

    # MessageHandler
    app.add_handler(MessageHandler(filters.REPLY & admin_filter & filters.Regex(r"^/ban$"), ban_cmd))
    app.add_handler(MessageHandler(filters.REPLY & admin_filter & filters.Regex(r"^/reply"), reply_cmd))
    app.add_handler(MessageHandler(filters.REPLY & admin_filter & filters.Regex(r"^/autoreply"), autoreply_cmd))

    # Callback handlers
    app.add_handler(CallbackQueryHandler(settings_callback, pattern=r"^settings\.*"))
    app.add_handler(CallbackQueryHandler(approve_yes_callback, pattern=r"^approve_yes$"))
    app.add_handler(CallbackQueryHandler(approve_no_callback, pattern=r"^approve_no$"))
    app.add_handler(CallbackQueryHandler(approve_status_callback, pattern=r"^approve_status\.*"))
    app.add_handler(CallbackQueryHandler(autoreply_callback, pattern=r"^autoreply\.*"))
    app.add_handler(CallbackQueryHandler(follow_spot_callback, pattern=r"^follow_\.*"))

    if Config.post_get("comments"):
        app.add_handler(MessageHandler(community_filter & filters.IS_AUTOMATIC_FORWARD, forwarded_post_msg))
    if Config.post_get("delete_anonymous_comments"):
        app.add_handler(
            MessageHandler(
                community_filter & filters.SenderChat.CHANNEL & ~filters.IS_AUTOMATIC_FORWARD,
                anonymous_comment_msg,
            )
        )

    app.add_handler(MessageHandler(community_filter & filters.REPLY, follow_spot_comment))


def add_jobs(app: Application):
    """Adds all the jobs to be scheduled to the application

    Args:
        app: supplied application
    """
    app.job_queue.run_daily(clean_pending_job, time=time(hour=5, tzinfo=utc))  # run each day at 05:00 utc
    app.job_queue.run_daily(db_backup_job, time=time(hour=5, tzinfo=utc))  # run each day at 05:00 utc
