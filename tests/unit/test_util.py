# pylint: disable=unused-argument redefined-outer-name
"""Tests the utility package"""
from datetime import datetime

import pytest
from telegram import CallbackQuery, Chat, Message, Update, User
from telegram.ext import Application, CallbackContext

from spotted.utils import EventInfo


@pytest.fixture(scope="class")
def app() -> Application:
    """Called once per at the beginning of this class.
    Creates a new Updater for testing

    Yields:
        telegram updater
    """
    # The telegram token is invented, is not valid, and it does not need to be
    return Application.builder().token("1234567890:qY9gv7pRJgFj4EVmN3Z1gfJOgQpCbh0vmp5").build()


@pytest.fixture(scope="class")
def get_user() -> User:
    """Creates a test user"""
    user_data = {
        "id": 100,
        "is_bot": False,
        "username": "u_name",
        "first_name": "f_name",
        "last_name": "l_name",
    }
    return User(**user_data)


@pytest.fixture(scope="class")
def get_chat() -> Chat:
    """Creates a test chat"""
    chat_data = {
        "id": 100,
        "type": "private",
        "username": "u_name",
        "first_name": "f_name",
        "last_name": "l_name",
        "bio": "bio",
    }
    return Chat(**chat_data)


@pytest.fixture(scope="class")
def get_message(get_user: User, get_chat: Chat) -> Message:
    """Creates a test message"""
    message_data = {
        "message_id": 1000,
        "date": datetime.now(),
        "chat": get_chat,
        "from_user": get_user,
        "forward_from": get_user,
        "forward_from_chat": get_chat,
        "forward_from_message_id": 1000,
        "forward_date": datetime.now(),
        "text": "Tets text",
    }
    return Message(**message_data)


@pytest.fixture(scope="class")
def get_callback_query(get_user: User, get_chat: Chat, get_message: Message) -> CallbackQuery:
    """Creates a test callback query"""
    callback_data = {
        "id": 10,
        "from_user": get_user,
        "message": get_message,
        "chat_instance": "Test chat",
        "data": "Test data",
        "inline_message_id": "1000",
        "game_short_name": "Test game",
    }
    return CallbackQuery(**callback_data)


@pytest.fixture(scope="function")
def message_update(app: Application, get_message: Message) -> tuple[Update, CallbackContext]:
    """Simulates a message update

    Returns:
        update and callback context
    """
    update = Update(0, message=get_message)
    callback_context = CallbackContext.from_update(update, app)
    return update, callback_context


@pytest.fixture(scope="function")
def callback_update(app: Application, get_callback_query: CallbackQuery) -> tuple[Update, CallbackContext]:
    """Simulates a callback query update

    Returns:
        update and callback context
    """
    update = Update(0, callback_query=get_callback_query)
    callback_context = CallbackContext.from_update(update, app)
    return update, callback_context


@pytest.fixture(scope="function")
def job_update(app: Application) -> CallbackContext:
    """Simulates a job update

    Returns:
        callback context
    """
    job = app.job_queue.run_once(lambda x: x, 10)
    callback_context = CallbackContext.from_update(job, app)
    return callback_context


class TestUtil:
    """Tests the utilities"""

    class TestInfoUtil:
        """Tests the EventInfo class"""

        def test_message_info(
            self, message_update: tuple[Update, CallbackContext], get_user: User, get_chat: Chat, get_message: Message
        ):
            """Tests the :meth:`from_message` :class:`EventInfo` initialization"""
            info = EventInfo.from_message(message_update[0], message_update[1])
            assert info.bot is not None
            assert info.context == message_update[1]
            assert info.update == message_update[0]
            assert info.message == get_message
            assert isinstance(info.bot_data, dict)
            assert isinstance(info.user_data, dict)

            assert info.chat_id == get_chat.id
            assert info.chat_type == get_chat.type
            assert info.is_private_chat == (get_chat.type == Chat.PRIVATE)

            assert info.text == get_message.text
            assert info.message_id == get_message.message_id
            assert info.is_valid_message_type is not None
            assert info.reply_markup == get_message.reply_markup

            assert info.user_id == get_user.id
            assert info.user_username == get_user.username
            assert info.user_name == get_user.name

            assert info.query_id is None
            assert info.query_data is None
            assert info.forward_from_id == get_message.forward_from_message_id
            assert info.forward_from_chat_id == get_message.forward_from_chat.id

        def test_callback_info(
            self,
            callback_update: tuple[Update, CallbackContext],
            get_user: User,
            get_chat: Chat,
            get_callback_query: CallbackQuery,
            get_message: Message,
        ):
            """Tests the :meth:`from_callback` :class:`EventInfo` initialization"""
            info = EventInfo.from_callback(callback_update[0], callback_update[1])
            assert info.bot is not None
            assert info.context == callback_update[1]
            assert info.update == callback_update[0]
            assert info.message == get_message
            assert isinstance(info.bot_data, dict)
            assert isinstance(info.user_data, dict)

            assert info.chat_id == get_chat.id
            assert info.chat_type == get_chat.type
            assert info.is_private_chat == (get_chat.type == Chat.PRIVATE)

            assert info.text == get_message.text
            assert info.message_id == get_message.message_id
            assert info.is_valid_message_type is not None
            assert info.reply_markup == get_message.reply_markup

            assert info.user_id == get_user.id
            assert info.user_username == get_user.username
            assert info.user_name == get_user.name

            assert info.query_id == get_callback_query.id
            assert info.query_data == get_callback_query.data
            assert info.forward_from_id == get_message.forward_from_message_id
            assert info.forward_from_chat_id == get_message.forward_from_chat.id

        def test_job_info(self, job_update: CallbackContext):
            """Tests the :meth:`from_job` :class:`EventInfo` initialization"""
            info = EventInfo.from_job(job_update)

            assert info.bot is not None
            assert info.context == job_update
            assert info.update is None
            assert info.message is None
            assert isinstance(info.bot_data, dict)
            assert info.user_data is None

            assert info.chat_id is None
            assert info.chat_type is None
            assert info.is_private_chat is None

            assert info.text is None
            assert info.message_id is None
            assert info.is_valid_message_type is False
            assert info.reply_markup is None

            assert info.user_id is None
            assert info.user_username is None
            assert info.user_name is None

            assert info.query_id is None
            assert info.query_data is None
            assert info.forward_from_id is None
            assert info.forward_from_chat_id is None
