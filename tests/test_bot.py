# pylint: disable=unused-argument,redefined-outer-name
"""Tests the bot functionality"""
import warnings
import os
import pytest
from telegram import Chat
from telegram.ext import Updater
from tests.utils import TelegramSimulator
from modules.data import config_map, read_md, get_abs_path, DbManager
from main import add_handlers


@pytest.fixture(scope="class")
def init_local_table() -> DbManager:
    """Called once per at the beginning of this class.
    Creates and initializes the local database
    """
    DbManager.db_path = ('data', 'db', 'test_db.sqlite3')
    DbManager.query_from_file("data", "db", "meme_db_del.sql")
    DbManager.query_from_file("data", "db", "meme_db_init.sql")
    yield DbManager
    os.remove(get_abs_path('data', 'db', 'test_db.sqlite3'))


@pytest.fixture(scope="function")
def local_table(init_local_table: DbManager) -> str:
    """Called once per at the beginning of each function.
    Resets the state of the database
    """
    init_local_table.query_from_file("data", "db", "meme_db_del.sql")
    init_local_table.query_from_file("data", "db", "meme_db_init.sql")


@pytest.fixture(scope="class")
def weave_telegram_library() -> TelegramSimulator:
    """Called once per at the beginning of this class.
    Weaves the telegram library to intercept the message sent by the bot

    Yields:
        telegram weaver
    """
    # The telegram token is invented, is not valid, and it does not need to be
    updater = Updater("1234567890:qY9gv7pRJgFj4EVmN3Z1gfJOgQpCbh0vmp5")
    add_handlers(updater.dispatcher)

    telegram = TelegramSimulator(updater=updater)

    return telegram


@pytest.fixture(scope="function")
def telegram(weave_telegram_library: TelegramSimulator) -> TelegramSimulator:
    """Called once per at the beginning of each function.
    Resets the telegram weaver object

    Yields:
        telegram weaver
    """
    weave_telegram_library.reset()
    return weave_telegram_library


@pytest.fixture(scope="function")
def admin_group(weave_telegram_library: TelegramSimulator) -> Chat:
    """Called once per at the beginning of each function.
    Returns an admin user

    Yields:
        admin user
    """
    group_id = config_map['meme']['group_id']
    return Chat(id=group_id, type="group")


class TestBot:
    """Tests the bot simulating the telegram API's responses"""

    class TestBotCommand:
        """Tests the bot commands"""

        def test_start_cmd(self, telegram: TelegramSimulator):
            """Tests the /start command.
            The bot sends the start response to the user
            """
            telegram.send_command("/start")
            assert telegram.last_message.text == read_md("start")

        def test_help_user_cmd(self, telegram: TelegramSimulator):
            """Tests the /help command.
            The bot sends the help response to the user
            """
            telegram.send_command("/help")
            assert telegram.last_message.text == read_md("help")

        def test_help_admin_cmd(self, telegram: TelegramSimulator, admin_group: Chat):
            """Tests the /help command.
            The bot sends the help response to the admins
            """
            telegram.send_command("/help", chat=admin_group)
            assert telegram.last_message.text == read_md("instructions")

        def test_rules_cmd(self, telegram: TelegramSimulator):
            """Tests the /rules command.
            The bot sends the rules response to the user
            """
            telegram.send_command("/rules")
            assert telegram.last_message.text == read_md("rules")
