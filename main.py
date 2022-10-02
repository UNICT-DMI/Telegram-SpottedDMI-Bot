"""Main module"""
from telegram.ext import Updater
from modules.data import Config
from modules.handlers import add_commands, add_handlers, add_jobs


def main():
    """Main function"""

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
