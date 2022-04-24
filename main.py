"""Main module"""
from telegram import BotCommand
from telegram.ext import Updater
from modules.data import Config
from modules.handlers import add_handlers, add_jobs


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


def main():
    """Main function
    """
    updater = Updater(Config.settings_get('token'),
                      request_kwargs={
                          'read_timeout': 20,
                          'connect_timeout': 20
                      },
                      use_context=True)
    add_commands(updater)
    add_handlers(updater.dispatcher)
    add_jobs(updater.dispatcher)

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
