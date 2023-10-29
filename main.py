"""Main module"""
from telegram.ext import Application
from modules.data import Config
from modules.handlers import add_commands, add_handlers, add_jobs


def main():
    """Main function"""

    application = Application.builder().token(Config.settings_get("token")).post_init(add_commands).build()
    add_handlers(application)
    add_jobs(application)

    application.run_polling()


if __name__ == "__main__":
    main()
