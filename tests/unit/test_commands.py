# pylint: disable=unused-argument,redefined-outer-name
"""Tests the bot commands"""
from datetime import datetime
import pytest
from pytest_mock import MockerFixture
from telegram import Update, User, Message, Chat, ParseMode
from telegram.ext import CallbackContext, Updater
from modules.data import DbManager, read_md
from modules.handlers import (start_cmd, help_cmd, rules_cmd, settings_cmd, stats_cmd)
from modules.handlers.constants import CHAT_PRIVATE_ERROR
from modules.utils import get_settings_kb
from modules.utils.keyboard_util import get_stats_kb


class FixtureRequest:
    """Fixture request class used for type hinting"""
    param: str


@pytest.fixture(scope="function")
def local_table(init_local_test_db: DbManager) -> DbManager:
    """Called once per at the beginning of each function.
    Resets the state of the database
    """
    init_local_test_db.query_from_file("data", "db", "meme_db_del.sql")
    init_local_test_db.query_from_file("data", "db", "meme_db_init.sql")
    return init_local_test_db


@pytest.fixture(scope="function")
def context(mocker: MockerFixture) -> CallbackContext:
    """Return a Telegram event, consisting of an Update and a CallbackContext"""
    dispatcher = Updater(token="1234567890:qY9gv7pRJgFj4EVmN3Z1gfJOgQpCbh0vmp5").dispatcher
    dispatcher.bot = mocker.Mock(return_value=None)
    return CallbackContext(dispatcher)


@pytest.fixture(scope="function", params=[Chat.GROUP])
def update(request: FixtureRequest) -> Update:
    """Return a Telegram event, consisting of an Update and a CallbackContext"""
    chat = Chat(id=0, type=request.param)
    user = User(id=0, first_name='user', is_bot=False, username='user')
    message = Message(message_id=0, from_user=user, chat=chat, date=datetime.now())
    return Update(update_id=0, message=message)


class TestCommands:
    """Tests the commands the bot is able to handle"""

    class TestBasicCommands:
        """Tests the bot's commands available to all users"""

        def test_start_cmd(self, update: Update, context: CallbackContext):
            """Tests the /start command.
            The bot sends the start response to the user
            """
            start_cmd(update, context)
            context.bot.send_message.assert_called_once_with(chat_id=update.message.chat_id,
                                                             text=read_md("start"),
                                                             parse_mode=ParseMode.MARKDOWN_V2,
                                                             disable_web_page_preview=True)

        def test_help_cmd(self, update: Update, context: CallbackContext):
            """Tests the /help command.
            The bot sends the help response to the user
            """
            help_cmd(update, context)
            context.bot.send_message.assert_called_once_with(chat_id=update.message.chat_id,
                                                             text=read_md("help"),
                                                             parse_mode=ParseMode.MARKDOWN_V2,
                                                             disable_web_page_preview=True)

        def test_rules_cmd(self, update: Update, context: CallbackContext):
            """Tests the /rules command.
            The bot sends the rules response to the user
            """
            rules_cmd(update, context)
            context.bot.send_message.assert_called_once_with(chat_id=update.message.chat_id,
                                                             text=read_md("rules"),
                                                             parse_mode=ParseMode.MARKDOWN_V2,
                                                             disable_web_page_preview=True)

        @pytest.mark.parametrize("update", [Chat.PRIVATE], indirect=True)
        def test_settings_cmd(self, update: Update, context: CallbackContext):
            """Tests the /settings command.
            The bot sends the settings response to the user
            """
            settings_cmd(update, context)
            context.bot.send_message.assert_called_once_with(chat_id=update.message.chat_id,
                                                             text="***Come vuoi che sia il tuo post:***",
                                                             parse_mode=ParseMode.MARKDOWN_V2,
                                                             reply_markup=get_settings_kb())

        @pytest.mark.parametrize("update", [Chat.GROUP, Chat.CHANNEL], indirect=True)
        def test_settings_cmd_not_private(self, update: Update, context: CallbackContext):
            """Tests the /settings command.
            The user is not in a private chat with the bot, so the bot sends an error message
            """
            settings_cmd(update, context)
            context.bot.send_message.assert_called_once_with(chat_id=update.message.chat_id, text=CHAT_PRIVATE_ERROR)

        def test_stats_cmd(self, update: Update, context: CallbackContext):
            """Tests the /stats command.
            The bot sends the stats response to the user
            """
            stats_cmd(update, context)
            context.bot.send_message.assert_called_once_with(chat_id=update.message.chat_id,
                                                             text="Che statistica ti interessa?",
                                                             reply_markup=get_stats_kb())
