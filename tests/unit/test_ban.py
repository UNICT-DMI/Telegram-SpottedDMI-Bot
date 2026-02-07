# pylint: disable=unused-argument,redefined-outer-name
"""Tests the ban command and execute_ban function"""

from unittest.mock import AsyncMock

import pytest

from spotted.data import Config, User
from spotted.handlers.ban import execute_ban
from spotted.utils import EventInfo


@pytest.mark.asyncio
class TestExecuteBan:
    """Tests the execute_ban function"""

    async def test_execute_ban_user_already_banned(self, test_table, mock_event_info: EventInfo, mock_bot: AsyncMock):
        """Tests execute_ban when the user is already banned.
        The bot should send a message saying the user is already banned
        """
        user_id = 100
        admin_group_id = Config.post_get("admin_group_id")

        # Create and ban the user first
        user = User(user_id)
        user.ban()

        # Execute the ban function
        await execute_ban(user_id, mock_event_info)

        # Verify that the bot sent a message indicating the user is already banned
        mock_bot.send_message.assert_called_once_with(chat_id=admin_group_id, text="L'utente è già bannato")

    async def test_execute_ban_user_not_banned(self, test_table, mock_event_info: EventInfo, mock_bot: AsyncMock):
        """Tests execute_ban when the user is not yet banned.
        The bot should ban the user and send confirmation messages
        """
        user_id = 200
        admin_group_id = Config.post_get("admin_group_id")

        # Ensure user is not banned initially
        user = User(user_id)
        assert not user.is_banned

        # Execute the ban function
        await execute_ban(user_id, mock_event_info)

        # Verify that the user is now banned
        user_after_ban = User(user_id)
        assert user_after_ban.is_banned

        # Verify that two messages were sent
        assert mock_bot.send_message.call_count == 2

        # Check the first call - message to admin group
        first_call = mock_bot.send_message.call_args_list[0]
        assert first_call.kwargs["chat_id"] == admin_group_id
        assert first_call.kwargs["text"] == "L'utente è stato bannato"

        # Check the second call - message to the banned user
        second_call = mock_bot.send_message.call_args_list[1]
        assert second_call.kwargs["chat_id"] == user_id
        assert "bannato da Spotted DMI" in second_call.kwargs["text"]
        assert "Grazie per il tuo contributo alla community" in second_call.kwargs["text"]

    async def test_execute_ban_user_receives_notification(
        self, test_table, mock_event_info: EventInfo, mock_bot: AsyncMock
    ):
        """Tests that the banned user receives the correct notification message"""
        user_id = 300
        expected_user_message = (
            "Grazie per il tuo contributo alla community, a causa "
            "di un tuo comportamento inadeguato sei stato bannato da Spotted DMI. Alla prossima!"
        )

        # Execute the ban function
        await execute_ban(user_id, mock_event_info)

        # Find the call that was sent to the user
        user_message_call = None
        for call in mock_bot.send_message.call_args_list:
            if call.kwargs["chat_id"] == user_id:
                user_message_call = call
                break

        # Assert that the user received the expected message
        assert user_message_call is not None
        assert user_message_call.kwargs["text"] == expected_user_message

    async def test_execute_ban_admin_receives_confirmation(
        self, test_table, mock_event_info: EventInfo, mock_bot: AsyncMock
    ):
        """Tests that the admin group receives the correct confirmation message"""
        user_id = 400
        admin_group_id = Config.post_get("admin_group_id")

        # Execute the ban function
        await execute_ban(user_id, mock_event_info)

        # Find the call that was sent to the admin group
        admin_message_call = None
        for call in mock_bot.send_message.call_args_list:
            if call.kwargs["chat_id"] == admin_group_id:
                admin_message_call = call
                break

        # Assert that the admin group received the expected message
        assert admin_message_call is not None
        assert admin_message_call.kwargs["text"] == "L'utente è stato bannato"

    async def test_execute_ban_multiple_users(self, test_table, mock_event_info: EventInfo, mock_bot: AsyncMock):
        """Tests banning multiple users sequentially"""
        user_ids = [500, 501, 502]

        for user_id in user_ids:
            # Reset the mock for each iteration
            mock_bot.reset_mock()

            # Execute the ban function
            await execute_ban(user_id, mock_event_info)

            # Verify user is banned
            user = User(user_id)
            assert user.is_banned

            # Verify messages were sent
            assert mock_bot.send_message.call_count == 2

    async def test_execute_ban_idempotent(self, test_table, mock_event_info: EventInfo, mock_bot: AsyncMock):
        """Tests that banning the same user multiple times is idempotent"""
        user_id = 600

        # First ban
        await execute_ban(user_id, mock_event_info)
        assert User(user_id).is_banned

        # Reset the mock to count new calls
        mock_bot.reset_mock()

        # Second ban attempt - should indicate user is already banned
        await execute_ban(user_id, mock_event_info)

        # Should only send one message (to admin group saying already banned)
        mock_bot.send_message.assert_called_once()
        call_args = mock_bot.send_message.call_args
        assert "già bannato" in call_args.kwargs["text"]
