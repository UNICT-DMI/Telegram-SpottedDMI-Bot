# pylint: disable=unused-argument,redefined-outer-name
"""Tests the clean_muted_users job handler"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from telegram.ext import Application, CallbackContext

from spotted.data import DbManager, User
from spotted.handlers.job_handlers import clean_muted_users


@pytest.fixture(scope="function")
def mock_bot() -> AsyncMock:
    """Create a mock bot instance"""
    bot = AsyncMock()
    bot.restrict_chat_member = AsyncMock(return_value=None)
    return bot


@pytest.fixture(scope="function")
def context_with_bot(mock_bot: AsyncMock) -> CallbackContext:
    """Return a CallbackContext with a mocked bot"""
    app = Application.builder().token("1234567890:qY9gv7pRJgFj4EVmN3Z1gfJOgQpCbh0vmp5").build()
    app.bot = mock_bot
    context = CallbackContext(app)
    return context


def create_muted_user(user_id: int, days_until_expiration: int):
    """Helper function to create a muted user with a specific expiration

    Args:
        user_id: The ID of the user to mute
        days_until_expiration: Days until the mute expires (negative means already expired)
    """
    mute_date = datetime.now()
    expire_date = datetime.now() + timedelta(days=days_until_expiration)

    DbManager.insert_into(
        table_name="muted_users",
        columns=("user_id", "mute_date", "expire_date"),
        values=(user_id, mute_date, expire_date),
    )


@pytest.mark.asyncio
class TestCleanMutedUsers:
    """Tests the clean_muted_users job handler"""

    async def test_clean_muted_users_no_expired_users(self, test_table, context_with_bot: CallbackContext):
        """Tests clean_muted_users when there are no expired muted users.
        The function should return early without doing anything
        """
        # Create some muted users that haven't expired yet
        create_muted_user(user_id=100, days_until_expiration=5)
        create_muted_user(user_id=101, days_until_expiration=10)

        # Run the clean function
        await clean_muted_users(context_with_bot)

        # Verify users are still muted
        assert User(100).is_muted
        assert User(101).is_muted

        # Verify no bot calls were made
        context_with_bot.bot.restrict_chat_member.assert_not_called()

    async def test_clean_muted_users_single_expired_user(
        self, test_table, context_with_bot: CallbackContext, mock_bot: AsyncMock
    ):
        """Tests clean_muted_users when there is one expired muted user.
        The function should unmute the user and remove them from the database
        """
        user_id = 200

        # Create an expired muted user (expired 1 day ago)
        create_muted_user(user_id=user_id, days_until_expiration=-1)

        # Verify user is muted before cleanup
        assert User(user_id).is_muted

        # Run the clean function
        await clean_muted_users(context_with_bot)

        # Verify user is no longer muted
        assert not User(user_id).is_muted

        # Verify the bot was called to unmute the user
        mock_bot.restrict_chat_member.assert_called_once()

    async def test_clean_muted_users_multiple_expired_users(
        self, test_table, context_with_bot: CallbackContext, mock_bot: AsyncMock
    ):
        """Tests clean_muted_users when there are multiple expired muted users.
        The function should unmute all expired users
        """
        expired_user_ids = [300, 301, 302]
        active_user_ids = [303, 304]

        # Create expired muted users
        for user_id in expired_user_ids:
            create_muted_user(user_id=user_id, days_until_expiration=-1)

        # Create active muted users (not expired)
        for user_id in active_user_ids:
            create_muted_user(user_id=user_id, days_until_expiration=5)

        # Verify all users are muted before cleanup
        for user_id in expired_user_ids + active_user_ids:
            assert User(user_id).is_muted

        # Run the clean function
        await clean_muted_users(context_with_bot)

        # Verify expired users are no longer muted
        for user_id in expired_user_ids:
            assert not User(user_id).is_muted

        # Verify active users are still muted
        for user_id in active_user_ids:
            assert User(user_id).is_muted

        # Verify the bot was called for each expired user
        assert mock_bot.restrict_chat_member.call_count == len(expired_user_ids)

    async def test_clean_muted_users_mixed_expiration_times(
        self, test_table, context_with_bot: CallbackContext, mock_bot: AsyncMock
    ):
        """Tests clean_muted_users with users having different expiration times.
        Only users with expired mutes should be cleaned
        """
        # Create users with different expiration times
        create_muted_user(user_id=400, days_until_expiration=-10)  # Expired 10 days ago
        create_muted_user(user_id=401, days_until_expiration=-1)  # Expired 1 day ago
        create_muted_user(user_id=402, days_until_expiration=0)  # Expires today (should be considered expired)
        create_muted_user(user_id=403, days_until_expiration=1)  # Expires tomorrow (not expired)
        create_muted_user(user_id=404, days_until_expiration=30)  # Expires in 30 days (not expired)

        # Run the clean function
        await clean_muted_users(context_with_bot)

        # Verify expired users are unmuted (400, 401, and possibly 402 depending on exact timing)
        assert not User(400).is_muted
        assert not User(401).is_muted

        # Verify future-expiring users are still muted
        assert User(403).is_muted
        assert User(404).is_muted

        # Verify the bot was called at least for the clearly expired users
        assert mock_bot.restrict_chat_member.call_count >= 2

    async def test_clean_muted_users_empty_database(self, test_table, context_with_bot: CallbackContext):
        """Tests clean_muted_users when there are no muted users at all.
        The function should return early without errors
        """
        # Ensure no muted users exist
        muted_users = DbManager.select_from(table_name="muted_users", select="user_id")
        assert len(muted_users) == 0

        # Run the clean function - should not raise any errors
        await clean_muted_users(context_with_bot)

        # Verify no bot calls were made
        context_with_bot.bot.restrict_chat_member.assert_not_called()

    async def test_clean_muted_users_database_cleanup(
        self, test_table, context_with_bot: CallbackContext, mock_bot: AsyncMock
    ):
        """Tests that clean_muted_users properly removes records from the database"""
        user_id = 500

        # Create an expired muted user
        create_muted_user(user_id=user_id, days_until_expiration=-1)

        # Verify the record exists in the database
        muted_records = DbManager.select_from(
            table_name="muted_users", select="user_id", where="user_id = %s", where_args=(user_id,)
        )
        assert len(muted_records) == 1

        # Run the clean function
        await clean_muted_users(context_with_bot)

        # Verify the record is removed from the database
        muted_records_after = DbManager.select_from(
            table_name="muted_users", select="user_id", where="user_id = %s", where_args=(user_id,)
        )
        assert len(muted_records_after) == 0

    async def test_clean_muted_users_bot_unmute_permissions(
        self, test_table, context_with_bot: CallbackContext, mock_bot: AsyncMock
    ):
        """Tests that clean_muted_users calls the bot with correct permissions to unmute"""
        user_id = 600

        # Create an expired muted user
        create_muted_user(user_id=user_id, days_until_expiration=-1)

        # Run the clean function
        await clean_muted_users(context_with_bot)

        # Verify the bot was called with the correct parameters
        mock_bot.restrict_chat_member.assert_called_once()
        call_args = mock_bot.restrict_chat_member.call_args

        # Check that the permissions allow the user to send messages
        assert call_args.kwargs["user_id"] == user_id
        permissions = call_args.kwargs["permissions"]
        assert permissions.can_send_messages is True
        assert permissions.can_send_other_messages is True
        assert permissions.can_add_web_page_previews is True
