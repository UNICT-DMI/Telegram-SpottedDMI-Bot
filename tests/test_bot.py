# pylint: disable=unused-argument,redefined-outer-name
"""Tests the bot functionality"""
import os
import pytest
from telegram import Chat
from tests.util import TelegramSimulator
from modules.data import config_map, read_md, get_abs_path, DbManager, User
from modules.handlers.constants import CHAT_PRIVATE_ERROR


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


@pytest.fixture(scope="function")
def telegram(local_table) -> TelegramSimulator:
    """Called once per at the beginning of each function.
    Resets the telegram weaver object

    Yields:
        telegram weaver
    """
    return TelegramSimulator()


@pytest.fixture(scope="class")
def admin_group() -> Chat:
    """Called once per at the beginning of each function.
    Returns an admin user

    Yields:
        admin user
    """
    group_id = config_map['meme']['group_id']
    return Chat(id=group_id, type="group")


@pytest.fixture(scope="class")
def public_group() -> Chat:
    """Called once per at the beginning of each function.
    Returns an admin user

    Yields:
        admin user
    """
    group_id = 1
    return Chat(id=group_id, type="group")


class TestBot:
    """Tests the bot simulating the telegram API's responses"""

    class TestBotBasicCommand:
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

    class TestBotSpotConversation:
        """Tests the spot conversation"""

        def test_spot_no_private_cmd(self, telegram: TelegramSimulator, public_group: Chat):
            """Tests the /spot command.
            Spot is not allowed in groups
            """
            telegram.send_command("/spot", chat=public_group)
            assert telegram.last_message.text == CHAT_PRIVATE_ERROR

        def test_spot_banned_cmd(self, telegram: TelegramSimulator):
            """Tests the /spot command.
            Spot is not allowed for banned users
            """
            User(1).ban()  # by default the user used by the telegram simulator has id 1
            telegram.send_command("/spot")
            assert telegram.last_message.text == "Sei stato bannato 😅"

        # TODO
        # def test_spot_pending_cmd(self, telegram: TelegramSimulator, local_table):
        #     """Tests the /spot command.
        #     Spot is not allowed for banned users
        #     """
        #     PendingPost.create({'from_user': {'id': 1}, 'message_id': 1}, 1, 1)
        #     telegram.send_command("/spot")
        #     assert telegram.last_message.text == "Hai già un post in approvazione 🧐"

        def test_spot_no_cmd(self, telegram: TelegramSimulator):
            """Tests the /spot command.
            Spot is not allowed for banned users
            """
            telegram.send_command("/spot")
            assert telegram.last_message.text == "Invia il post che vuoi pubblicare"

            telegram.send_message("Test spot")
            assert telegram.last_message.text == "Sei sicuro di voler publicare questo post?"
            assert telegram.last_message.reply_to_message is not None

            telegram.send_callback_query(text="No")
            assert telegram.last_message.text == "Va bene, alla prossima 🙃"

        def test_spot_si_cmd(self, telegram: TelegramSimulator):
            """Tests the /spot command.
            Spot is not allowed for banned users
            """
            telegram.send_command("/spot")
            assert telegram.last_message.text == "Invia il post che vuoi pubblicare"

            telegram.send_message("Test spot")
            assert telegram.last_message.text == "Sei sicuro di voler publicare questo post?"
            assert telegram.last_message.reply_to_message is not None

            telegram.send_callback_query(text="Si")
            assert telegram.last_message.text == "Il tuo post è in fase di valutazione\n"\
                f"Una volta pubblicato, lo potrai trovare su {config_map['meme']['channel_tag']}"

        def test_spot_cancel_cmd(self, telegram: TelegramSimulator):
            """Tests the /spot command.
            Cancel the conversation
            """
            telegram.send_command("/spot")
            assert telegram.last_message.text == "Invia il post che vuoi pubblicare"

            telegram.send_command("/cancel")
            assert telegram.last_message.text == read_md("spot_cancel")
