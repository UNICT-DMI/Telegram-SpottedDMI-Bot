# pylint: disable=unused-argument,redefined-outer-name
"""Tests for mute_cmd, unmute_cmd, warn_cmd, and execute_warn"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from telegram import Chat, Message, Update
from telegram import User as TelegramUser
from telegram.ext import CallbackContext

from spotted.data import Config, DbManager, PendingPost, User
from spotted.handlers.mute import mute_cmd
from spotted.handlers.unmute import unmute_cmd
from spotted.handlers.warn import execute_warn, warn_cmd
from spotted.utils import EventInfo


@pytest.fixture(scope="function")
def mock_event_info(mock_bot: AsyncMock, context_with_bot: CallbackContext) -> EventInfo:
    """Create a mock EventInfo instance with additional mocking for warn/mute commands"""
    info = MagicMock(spec=EventInfo)
    info.bot = mock_bot
    info.context = context_with_bot
    info.chat_id = Config.post_get("admin_group_id")
    info.user_id = 999  # Admin user
    info.message = MagicMock()
    info.message.delete = AsyncMock()
    info.edit_inline_keyboard = AsyncMock()
    return info


def create_update_with_reply(admin_id: int, reply_user_id: int, chat_id: int, message_id: int = 123, bot=None):
    """Helper to create an Update with a reply_to_message"""
    admin_user = TelegramUser(id=admin_id, first_name="Admin", is_bot=False)
    reply_user = TelegramUser(id=reply_user_id, first_name="User", is_bot=False)
    chat = Chat(id=chat_id, type=Chat.GROUP)

    reply_message = Message(
        message_id=message_id, from_user=reply_user, chat=chat, date=datetime.now(), text="Original message"
    )
    if bot:
        reply_message._bot = bot  # pylint: disable=protected-access

    message = Message(
        message_id=124,
        from_user=admin_user,
        chat=chat,
        date=datetime.now(),
        text="/command",
        reply_to_message=reply_message,
    )
    if bot:
        message._bot = bot  # pylint: disable=protected-access

    return Update(update_id=0, message=message)


@pytest.mark.asyncio
class TestMuteCmd:
    """Tests for the mute_cmd function"""

    async def test_mute_cmd_not_admin(self, test_table, context_with_bot: CallbackContext, mock_bot: AsyncMock):
        """Tests mute_cmd when user is not an admin.
        Should send error message and delete the command
        """
        community_group_id = Config.post_get("community_group_id")
        non_admin_id = 888
        user_to_mute = 100

        update = create_update_with_reply(non_admin_id, user_to_mute, community_group_id, bot=mock_bot)
        context_with_bot.args = None

        await mute_cmd(update, context_with_bot)

        # Verify error message was sent to the non-admin
        calls = [call for call in mock_bot.send_message.call_args_list if call.kwargs.get("chat_id") == non_admin_id]
        assert len(calls) == 1
        assert "Non sei un admin" in calls[0].kwargs["text"]

    async def test_mute_cmd_no_reply(self, test_table, context_with_bot: CallbackContext, mock_bot: AsyncMock):
        """Tests mute_cmd when there's no reply_to_message.
        Should send usage instructions
        """
        admin_id = 999
        chat = Chat(id=Config.post_get("community_group_id"), type=Chat.GROUP)
        admin_user = TelegramUser(id=admin_id, first_name="Admin", is_bot=False)
        message = Message(message_id=124, from_user=admin_user, chat=chat, date=datetime.now(), text="/mute")
        message._bot = mock_bot  # pylint: disable=protected-access
        update = Update(update_id=0, message=message)
        context_with_bot.args = None

        await mute_cmd(update, context_with_bot)

        # Verify usage message was sent
        calls = [call for call in mock_bot.send_message.call_args_list if call.kwargs.get("chat_id") == admin_id]
        assert len(calls) == 1
        assert "Per mutare rispondi ad un commento con /mute" in calls[0].kwargs["text"]

    async def test_mute_cmd_default_duration(self, test_table, context_with_bot: CallbackContext, mock_bot: AsyncMock):
        """Tests mute_cmd with default duration (no args).
        Should mute user for default number of days
        """
        admin_id = 999
        user_to_mute = 200
        community_group_id = Config.post_get("community_group_id")

        update = create_update_with_reply(admin_id, user_to_mute, community_group_id, bot=mock_bot)
        context_with_bot.args = []

        await mute_cmd(update, context_with_bot)

        # Verify user is muted
        assert User(user_to_mute).is_muted

        # Verify bot called restrict_chat_member
        mock_bot.restrict_chat_member.assert_called_once()
        call_args = mock_bot.restrict_chat_member.call_args
        assert call_args.kwargs["user_id"] == user_to_mute
        assert call_args.kwargs["permissions"].can_send_messages is False

        # Verify notifications sent
        assert mock_bot.send_message.call_count >= 2

    async def test_mute_cmd_custom_duration(self, test_table, context_with_bot: CallbackContext, mock_bot: AsyncMock):
        """Tests mute_cmd with custom duration.
        Should mute user for specified number of days
        """
        admin_id = 999
        user_to_mute = 300
        days = 14
        community_group_id = Config.post_get("community_group_id")

        update = create_update_with_reply(admin_id, user_to_mute, community_group_id, bot=mock_bot)
        context_with_bot.args = [str(days)]

        await mute_cmd(update, context_with_bot)

        # Verify user is muted
        assert User(user_to_mute).is_muted

        # Verify the notification mentions the correct duration
        user_message_call = None
        for call in mock_bot.send_message.call_args_list:
            if call.kwargs.get("chat_id") == user_to_mute:
                user_message_call = call
                break

        assert user_message_call is not None
        assert "14 giorni" in user_message_call.kwargs["text"]

    async def test_mute_cmd_invalid_duration(self, test_table, context_with_bot: CallbackContext, mock_bot: AsyncMock):
        """Tests mute_cmd with invalid duration argument.
        Should fall back to default duration
        """
        admin_id = 999
        user_to_mute = 400
        community_group_id = Config.post_get("community_group_id")

        update = create_update_with_reply(admin_id, user_to_mute, community_group_id, bot=mock_bot)
        context_with_bot.args = ["invalid"]

        await mute_cmd(update, context_with_bot)

        # Verify user is still muted with default duration
        assert User(user_to_mute).is_muted


@pytest.mark.asyncio
class TestUnmuteCmd:
    """Tests for the unmute_cmd function"""

    async def test_unmute_cmd_no_args(self, test_table, context_with_bot: CallbackContext, mock_bot: AsyncMock):
        """Tests unmute_cmd without arguments.
        Should display list of currently muted users
        """
        admin_id = 999
        chat = Chat(id=Config.post_get("admin_group_id"), type=Chat.GROUP)
        admin_user = TelegramUser(id=admin_id, first_name="Admin", is_bot=False)
        message = Message(message_id=124, from_user=admin_user, chat=chat, date=datetime.now(), text="/unmute")
        update = Update(update_id=0, message=message)
        context_with_bot.args = None

        # Create some muted users
        mute_date = datetime.now()
        expire_date = datetime.now() + timedelta(days=7)
        DbManager.insert_into(
            table_name="muted_users",
            columns=("user_id", "mute_date", "expire_date"),
            values=(100, mute_date, expire_date),
        )

        await unmute_cmd(update, context_with_bot)

        # Verify usage message was sent with list of muted users
        mock_bot.send_message.assert_called_once()
        call_args = mock_bot.send_message.call_args
        assert "[uso]: /unmute" in call_args.kwargs["text"]
        assert "100" in call_args.kwargs["text"]

    async def test_unmute_cmd_single_user(self, test_table, context_with_bot: CallbackContext, mock_bot: AsyncMock):
        """Tests unmute_cmd with a single user ID.
        Should unmute the user
        """
        admin_id = 999
        user_to_unmute = 200
        chat = Chat(id=Config.post_get("admin_group_id"), type=Chat.GROUP)
        admin_user = TelegramUser(id=admin_id, first_name="Admin", is_bot=False)
        message = Message(message_id=124, from_user=admin_user, chat=chat, date=datetime.now(), text="/unmute 200")
        update = Update(update_id=0, message=message)
        context_with_bot.args = [str(user_to_unmute)]

        # Mute the user first
        mute_date = datetime.now()
        expire_date = datetime.now() + timedelta(days=7)
        DbManager.insert_into(
            table_name="muted_users",
            columns=("user_id", "mute_date", "expire_date"),
            values=(user_to_unmute, mute_date, expire_date),
        )
        assert User(user_to_unmute).is_muted

        await unmute_cmd(update, context_with_bot)

        # Verify user is unmuted
        assert not User(user_to_unmute).is_muted

        # Verify success message sent
        admin_message = None
        for call in mock_bot.send_message.call_args_list:
            if call.kwargs.get("chat_id") == Config.post_get("admin_group_id"):
                admin_message = call
                break

        assert admin_message is not None
        assert "senza errori" in admin_message.kwargs["text"]

    async def test_unmute_cmd_multiple_users(self, test_table, context_with_bot: CallbackContext, mock_bot: AsyncMock):
        """Tests unmute_cmd with multiple user IDs.
        Should unmute all users
        """
        admin_id = 999
        users_to_unmute = [300, 301, 302]
        chat = Chat(id=Config.post_get("admin_group_id"), type=Chat.GROUP)
        admin_user = TelegramUser(id=admin_id, first_name="Admin", is_bot=False)
        message = Message(
            message_id=124, from_user=admin_user, chat=chat, date=datetime.now(), text="/unmute 300 301 302"
        )
        update = Update(update_id=0, message=message)
        context_with_bot.args = [str(uid) for uid in users_to_unmute]

        # Mute all users first
        mute_date = datetime.now()
        expire_date = datetime.now() + timedelta(days=7)
        for user_id in users_to_unmute:
            DbManager.insert_into(
                table_name="muted_users",
                columns=("user_id", "mute_date", "expire_date"),
                values=(user_id, mute_date, expire_date),
            )
            assert User(user_id).is_muted

        await unmute_cmd(update, context_with_bot)

        # Verify all users are unmuted
        for user_id in users_to_unmute:
            assert not User(user_id).is_muted

    async def test_unmute_cmd_invalid_user_id(self, test_table, context_with_bot: CallbackContext, mock_bot: AsyncMock):
        """Tests unmute_cmd with invalid user ID.
        Should report error for invalid IDs
        """
        admin_id = 999
        chat = Chat(id=Config.post_get("admin_group_id"), type=Chat.GROUP)
        admin_user = TelegramUser(id=admin_id, first_name="Admin", is_bot=False)
        message = Message(message_id=124, from_user=admin_user, chat=chat, date=datetime.now(), text="/unmute invalid")
        update = Update(update_id=0, message=message)
        context_with_bot.args = ["invalid"]

        await unmute_cmd(update, context_with_bot)

        # Verify error message sent
        admin_message = None
        for call in mock_bot.send_message.call_args_list:
            if call.kwargs.get("chat_id") == Config.post_get("admin_group_id"):
                admin_message = call
                break

        assert admin_message is not None
        assert "con errori" in admin_message.kwargs["text"]


@pytest.mark.asyncio
class TestWarnCmd:
    """Tests for the warn_cmd function"""

    async def test_warn_cmd_not_admin(self, test_table, context_with_bot: CallbackContext, mock_bot: AsyncMock):
        """Tests warn_cmd when user is not an admin.
        Should send error message and delete command
        """
        non_admin_id = 888
        user_to_warn = 100
        community_group_id = Config.post_get("community_group_id")

        update = create_update_with_reply(non_admin_id, user_to_warn, community_group_id, bot=mock_bot)
        context_with_bot.args = None

        await warn_cmd(update, context_with_bot)

        # Verify error message was sent
        calls = [call for call in mock_bot.send_message.call_args_list if call.kwargs.get("chat_id") == non_admin_id]
        assert len(calls) == 1
        assert "Non sei admin" in calls[0].kwargs["text"]

    async def test_warn_cmd_no_reply(self, test_table, context_with_bot: CallbackContext, mock_bot: AsyncMock):
        """Tests warn_cmd when there's no reply_to_message.
        Should send usage instructions
        """
        admin_id = 999
        chat = Chat(id=Config.post_get("admin_group_id"), type=Chat.GROUP)
        admin_user = TelegramUser(id=admin_id, first_name="Admin", is_bot=False)
        message = Message(message_id=124, from_user=admin_user, chat=chat, date=datetime.now(), text="/warn")
        message._bot = mock_bot  # pylint: disable=protected-access
        update = Update(update_id=0, message=message)
        context_with_bot.args = None

        await warn_cmd(update, context_with_bot)

        # Verify usage message was sent
        calls = [
            call
            for call in mock_bot.send_message.call_args_list
            if call.kwargs.get("chat_id") == Config.post_get("admin_group_id")
        ]
        assert len(calls) == 1
        assert "Per warnare rispondi" in calls[0].kwargs["text"]

    async def test_warn_cmd_no_reason(self, test_table, context_with_bot: CallbackContext, mock_bot: AsyncMock):
        """Tests warn_cmd without a reason (no args).
        Should send usage instructions
        """
        admin_id = 999
        user_to_warn = 200
        community_group_id = Config.post_get("community_group_id")

        update = create_update_with_reply(admin_id, user_to_warn, community_group_id, bot=mock_bot)
        context_with_bot.args = []

        await warn_cmd(update, context_with_bot)

        # Verify usage message was sent
        calls = [
            call
            for call in mock_bot.send_message.call_args_list
            if call.kwargs.get("chat_id") == Config.post_get("admin_group_id")
        ]
        assert len(calls) == 1
        assert "Per warnare rispondi" in calls[0].kwargs["text"]

    async def test_warn_cmd_community_message(self, test_table, context_with_bot: CallbackContext, mock_bot: AsyncMock):
        """Tests warn_cmd when replying to a community group message.
        Should warn the user and delete the command
        """
        admin_id = 999
        user_to_warn = 300
        community_group_id = Config.post_get("community_group_id")

        update = create_update_with_reply(admin_id, user_to_warn, community_group_id, bot=mock_bot)
        context_with_bot.args = ["spam", "behavior"]

        await warn_cmd(update, context_with_bot)

        # Verify user has a warn
        assert User(user_to_warn).get_n_warns() == 1

        # Verify notification sent to user
        user_calls = [
            call for call in mock_bot.send_message.call_args_list if call.kwargs.get("chat_id") == user_to_warn
        ]
        assert len(user_calls) == 1
        assert "warnato" in user_calls[0].kwargs["text"]
        assert "spam behavior" in user_calls[0].kwargs["text"]

    async def test_warn_cmd_pending_post(self, test_table, context_with_bot: CallbackContext, mock_bot: AsyncMock):
        """Tests warn_cmd when replying to a pending post.
        Should warn the user and delete the pending post
        """
        admin_id = 999
        user_to_warn = 400
        admin_group_id = Config.post_get("admin_group_id")
        g_message_id = 123

        # Create a pending post
        PendingPost.create(
            user_message=MagicMock(
                message_id=1, chat_id=user_to_warn, from_user=MagicMock(id=user_to_warn, username="testuser")
            ),
            admin_group_id=admin_group_id,
            g_message_id=g_message_id,
        )

        update = create_update_with_reply(admin_id, user_to_warn, admin_group_id, g_message_id)
        context_with_bot.args = ["inappropriate", "content"]

        await warn_cmd(update, context_with_bot)

        # Verify user has a warn
        assert User(user_to_warn).get_n_warns() == 1

        # Verify pending post was deleted
        assert PendingPost.from_group(admin_group_id=admin_group_id, g_message_id=g_message_id) is None


@pytest.mark.asyncio
class TestExecuteWarn:
    """Tests for the execute_warn function"""

    async def test_execute_warn_first_warning(self, test_table, mock_event_info: EventInfo, mock_bot: AsyncMock):
        """Tests execute_warn for a user's first warning.
        Should add warn and send notification
        """
        user_id = 500
        comment = "First offense"

        await execute_warn(mock_event_info, user_id, comment, from_community=False)

        # Verify user has 1 warn
        assert User(user_id).get_n_warns() == 1

        # Verify messages sent
        assert mock_bot.send_message.call_count == 2

        # Verify user notification
        user_calls = [call for call in mock_bot.send_message.call_args_list if call.kwargs.get("chat_id") == user_id]
        assert len(user_calls) == 1
        assert "warnato" in user_calls[0].kwargs["text"]
        assert comment in user_calls[0].kwargs["text"]

    async def test_execute_warn_multiple_warnings(self, test_table, mock_event_info: EventInfo, mock_bot: AsyncMock):
        """Tests execute_warn for a user with multiple warnings.
        Should track warning count correctly
        """
        user_id = 600

        # Add first warning with a specific time
        warn_date_1 = datetime.now() - timedelta(seconds=2)
        DbManager.insert_into(
            table_name="warned_users",
            columns=("user_id", "warn_date", "expire_date"),
            values=(user_id, warn_date_1, warn_date_1 + timedelta(days=Config.post_get("warn_expiration_days"))),
        )
        assert User(user_id).get_n_warns() == 1

        # Add second warning with a different time
        warn_date_2 = datetime.now()
        DbManager.insert_into(
            table_name="warned_users",
            columns=("user_id", "warn_date", "expire_date"),
            values=(user_id, warn_date_2, warn_date_2 + timedelta(days=Config.post_get("warn_expiration_days"))),
        )
        assert User(user_id).get_n_warns() == 2

    async def test_execute_warn_auto_ban(self, test_table, mock_event_info: EventInfo, mock_bot: AsyncMock):
        """Tests execute_warn when user reaches max warnings.
        Should automatically ban the user
        """
        user_id = 700
        max_warns = Config.post_get("max_n_warns")

        # Add warnings up to max - 1
        for i in range(max_warns - 1):
            warn_date = datetime.now() - timedelta(seconds=max_warns - i)
            DbManager.insert_into(
                table_name="warned_users",
                columns=("user_id", "warn_date", "expire_date"),
                values=(user_id, warn_date, warn_date + timedelta(days=Config.post_get("warn_expiration_days"))),
            )

        # Add the last warning that should trigger the ban
        await execute_warn(mock_event_info, user_id, "Final warning", from_community=False)

        # Verify user is banned after reaching max warns
        assert User(user_id).is_banned

    async def test_execute_warn_from_community_deletes_message(
        self, test_table, mock_event_info: EventInfo, mock_bot: AsyncMock
    ):
        """Tests execute_warn with from_community=True.
        Should delete the command message
        """
        user_id = 800
        comment = "Community violation"

        await execute_warn(mock_event_info, user_id, comment, from_community=True)

        # Verify message was deleted
        mock_event_info.message.delete.assert_called_once()

    async def test_execute_warn_not_from_community_no_delete(
        self, test_table, mock_event_info: EventInfo, mock_bot: AsyncMock
    ):
        """Tests execute_warn with from_community=False.
        Should not delete the command message
        """
        user_id = 900
        comment = "Admin group violation"

        await execute_warn(mock_event_info, user_id, comment, from_community=False)

        # Verify message was not deleted
        mock_event_info.message.delete.assert_not_called()

    async def test_execute_warn_admin_notification(self, test_table, mock_event_info: EventInfo, mock_bot: AsyncMock):
        """Tests that execute_warn sends notification to admin group"""
        user_id = 1000
        comment = "Test violation"

        await execute_warn(mock_event_info, user_id, comment, from_community=False)

        # Verify admin group received notification
        admin_calls = [
            call
            for call in mock_bot.send_message.call_args_list
            if call.kwargs.get("chat_id") == Config.post_get("admin_group_id")
        ]
        assert len(admin_calls) == 1
        assert str(user_id) in admin_calls[0].kwargs["text"]
        assert comment in admin_calls[0].kwargs["text"]
