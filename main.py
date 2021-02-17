"""Main module"""
# region imports
# libs
import warnings
from datetime import time
from pytz import utc
# telegram
from telegram import BotCommand
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler,\
     Filters, Dispatcher
# debug
from modules.debug.log_manager import log_message
# data
from modules.data.data_reader import config_map
# handlers
from modules.handlers.command_handlers import STATE, start_cmd, help_cmd, settings_cmd, post_cmd, ban_cmd, reply_cmd,\
    clean_pending_cmd, post_msg, rules_cmd, sban_cmd, cancel_cmd, stats_cmd, forwarded_post_msg, report_post, report_cmd, \
    report_user_msg, report_user_sent_msg
from modules.handlers.callback_handlers import meme_callback, stats_callback
from modules.handlers.job_handlers import clean_pending_job
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

    # Conversation handler
    dp.add_handler(
        ConversationHandler(entry_points=[CommandHandler("spot", post_cmd)],
                            states={
                                STATE['posting']: [MessageHandler(~Filters.command, post_msg)],
                                STATE['confirm']: [CallbackQueryHandler(meme_callback, pattern=r"^meme_confirm\.*")]
                            },
                            fallbacks=[CommandHandler("cancel", cancel_cmd)],
                            allow_reentry=False))

    dp.add_handler(
        ConversationHandler(entry_points=[CommandHandler("report", report_cmd)],
                            states={
                                STATE['reporting_user']: [MessageHandler(~Filters.command, report_user_msg)],
                                STATE['reporting_user_reason']: [MessageHandler(~Filters.command, report_user_msg)],
                                STATE['sending_user_report']: [MessageHandler(~Filters.command, report_user_sent_msg)]
                            },
                            fallbacks=[CommandHandler("cancel", cancel_cmd)],
                            allow_reentry=False))

    dp.add_handler(
        ConversationHandler(entry_points=[CallbackQueryHandler(meme_callback, pattern=r"^meme_report\.*")],
                            states={
                                STATE['reporting_spot']: [MessageHandler(~Filters.command, report_post)],
                            },
                            fallbacks=[CommandHandler("cancel", cancel_cmd)],
                            allow_reentry=False,
                            per_chat=False))
    # Command handlers
    dp.add_handler(CommandHandler("start", start_cmd))
    dp.add_handler(CommandHandler("help", help_cmd))
    dp.add_handler(CommandHandler("rules", rules_cmd))
    dp.add_handler(CommandHandler("stats", stats_cmd))
    dp.add_handler(CommandHandler("settings", settings_cmd))
    dp.add_handler(CommandHandler("sban", sban_cmd))
    dp.add_handler(CommandHandler("clean_pending", clean_pending_cmd))
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
