"""Main module"""
# region imports
# libs
import warnings
# telegram
from telegram import BotCommand
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler,\
     Filters, Dispatcher
# debug
from modules.debug.log_manager import log_message
# data
from modules.data.data_reader import config_map
# commands
from modules.handlers.command_handlers import STATE, start_cmd, help_cmd, settings_cmd, post_cmd, ban_cmd, reply_cmd,\
    clean_pending_cmd, post_msg, rules_cmd, sban_cmd, cancel_cmd, stats_cmd, forwarded_post_msg
from modules.handlers.callback_handlers import meme_callback, stats_callback
# endregion


def add_commands(up: Updater):
    """Adds the list of commands with their description to the bot

    Args:
        up (Updater): supplyed Updater
    """
    commands = [
        BotCommand("start", "presentazione iniziale del bot"),
        BotCommand("spot", "inizia a spottare"),
        BotCommand("help ", "funzionamento e scopo del bot"),
        BotCommand("rules ", "regole da tenere a mente"),
        BotCommand("stats", "visualizza statistiche sugli spot"),
        BotCommand("settings", "cambia le impostazioni di privacy")
    ]
    up.bot.set_my_commands(commands=commands)


def add_handlers(dp: Dispatcher):
    """Adds all the needed handlers to the dipatcher

    Args:
        dp (Dispatcher): supplyed dispacther
    """
    if config_map['debug']['local_log']:  # add MessageHandler only if log_message is enabled
        dp.add_handler(MessageHandler(Filters.all, log_message), 1)

    # Command handlers
    dp.add_handler(CommandHandler("start", start_cmd))
    dp.add_handler(CommandHandler("help", help_cmd))
    dp.add_handler(CommandHandler("rules", rules_cmd))
    dp.add_handler(CommandHandler("stats", stats_cmd))
    dp.add_handler(CommandHandler("settings", settings_cmd))
    dp.add_handler(CommandHandler("sban", sban_cmd))
    dp.add_handler(CommandHandler("clean_pending", clean_pending_cmd))

    # Conversation handler
    dp.add_handler(
        ConversationHandler(entry_points=[CommandHandler("spot", post_cmd)],
                            states={
                                STATE['posting']: [MessageHandler(~Filters.command, post_msg)],
                                STATE['confirm']: [CallbackQueryHandler(meme_callback, pattern=r"meme_confirm_\.*")]
                            },
                            fallbacks=[
                                CommandHandler("cancel", cancel_cmd),
                            ],
                            allow_reentry=False))
    # MessageHandler
    dp.add_handler(MessageHandler(Filters.reply & Filters.regex(r"^/ban$"), ban_cmd))
    dp.add_handler(MessageHandler(Filters.reply & Filters.regex(r"^/reply"), reply_cmd))

    # Callback handlers
    dp.add_handler(CallbackQueryHandler(meme_callback, pattern=r"^meme_\.*"))
    dp.add_handler(CallbackQueryHandler(stats_callback, pattern=r"^stats_\.*"))

    if config_map['meme']['comments']:
        dp.add_handler(MessageHandler(Filters.forwarded, forwarded_post_msg))


def main():
    """Main function
    """
    updater = Updater(config_map['token'], request_kwargs={'read_timeout': 20, 'connect_timeout': 20}, use_context=True)
    add_commands(updater)
    add_handlers(updater.dispatcher)

    updater.start_polling()
    updater.idle()


warnings.filterwarnings("ignore",
                        message="If 'per_message=False', 'CallbackQueryHandler' will not be tracked for every message.")
if __name__ == "__main__":
    main()
