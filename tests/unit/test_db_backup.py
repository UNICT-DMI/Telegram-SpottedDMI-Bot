# pylint: disable=unused-argument,redefined-outer-name
"""Tests the db_backup command and job handler with different backup_chat_id values"""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from telegram import Chat, Message, Update, User
from telegram.error import TelegramError
from telegram.ext import Application, CallbackContext

from spotted.data import Config
from spotted.handlers.db_backup import db_backup_cmd
from spotted.handlers.job_handlers import db_backup_job


@pytest.fixture(scope="function")
def mock_bot() -> AsyncMock:
    """Create a mock bot instance"""
    bot = AsyncMock()
    bot.send_message = AsyncMock(return_value=None)
    bot.send_document = AsyncMock(return_value=None)
    return bot


@pytest.fixture(scope="function")
def context_with_bot(mock_bot: AsyncMock) -> CallbackContext:
    """Return a CallbackContext with a mocked bot"""
    app = Application.builder().token("1234567890:qY9gv7pRJgFj4EVmN3Z1gfJOgQpCbh0vmp5").build()
    app.bot = mock_bot
    context = CallbackContext(app)
    return context


@pytest.fixture(scope="function")
def update() -> Update:
    """Return a Telegram Update with a message from the admin group"""
    admin_group_id = Config.post_get("admin_group_id")
    chat = Chat(id=admin_group_id, type=Chat.GROUP)
    user = User(id=999, first_name="admin", is_bot=False, username="admin")
    message = Message(message_id=42, from_user=user, chat=chat, date=datetime.now())
    return Update(update_id=0, message=message)


@pytest.fixture(autouse=True)
def reset_backup_chat_id():
    """Reset backup_chat_id to its default value (0) after each test"""
    yield
    Config.override_settings({"debug": {"backup_chat_id": 0}})


@pytest.mark.asyncio
class TestDbBackupCmd:
    """Tests the /db_backup command handler with different backup_chat_id values"""

    async def test_backup_cmd_disabled_when_chat_id_is_zero(
        self, update: Update, context_with_bot: CallbackContext, mock_bot: AsyncMock
    ):
        """When backup_chat_id is 0 (default), the /db_backup command should
        inform the user that the feature is disabled and not send any backup.
        """
        Config.override_settings({"debug": {"backup_chat_id": 0}})

        await db_backup_cmd(update, context_with_bot)

        # Should send a "disabled" message back to the chat
        mock_bot.send_message.assert_called_once_with(
            chat_id=update.message.chat_id,
            reply_to_message_id=update.message.message_id,
            text="La funzionalità di backup è disabilitata. Imposta `backup_chat_id` per abilitarla.",
        )
        # Should NOT attempt to send a document
        mock_bot.send_document.assert_not_called()

    @patch("spotted.handlers.job_handlers.get_backup", return_value=b"fake_db_content")
    async def test_backup_cmd_sends_to_admin_group(
        self, mock_get_backup, update: Update, context_with_bot: CallbackContext, mock_bot: AsyncMock
    ):
        """When backup_chat_id equals admin_group_id, the /db_backup command should
        send the backup document to the admin group and NOT send a separate confirmation.
        """
        admin_group_id = Config.post_get("admin_group_id")
        Config.override_settings({"debug": {"backup_chat_id": admin_group_id}})

        await db_backup_cmd(update, context_with_bot)

        # Should send the backup document to the admin group
        mock_bot.send_document.assert_called_once()
        call_kwargs = mock_bot.send_document.call_args
        assert call_kwargs.kwargs["chat_id"] == admin_group_id

        # Should NOT send a separate text confirmation (same chat)
        mock_bot.send_message.assert_not_called()

    @patch("spotted.handlers.job_handlers.get_backup", return_value=b"fake_db_content")
    async def test_backup_cmd_sends_to_different_chat(
        self, mock_get_backup, update: Update, context_with_bot: CallbackContext, mock_bot: AsyncMock
    ):
        """When backup_chat_id is set to a different valid chat, the /db_backup command should
        send the backup document to that chat and a confirmation to the admin group.
        """
        different_chat_id = -999
        Config.override_settings({"debug": {"backup_chat_id": different_chat_id}})

        await db_backup_cmd(update, context_with_bot)

        # Should send the backup document to the specified chat
        mock_bot.send_document.assert_called_once()
        call_kwargs = mock_bot.send_document.call_args
        assert call_kwargs.kwargs["chat_id"] == different_chat_id

        # Should also send a text confirmation to the admin group
        admin_group_id = Config.post_get("admin_group_id")
        mock_bot.send_message.assert_called_once_with(chat_id=admin_group_id, text="✅ Backup effettuato con successo")


@pytest.mark.asyncio
class TestDbBackupJob:
    """Tests the db_backup_job scheduled handler with different backup_chat_id values"""

    @patch("spotted.handlers.job_handlers.get_backup", return_value=b"fake_db_content")
    async def test_backup_job_sends_to_admin_group(
        self, mock_get_backup, context_with_bot: CallbackContext, mock_bot: AsyncMock
    ):
        """When backup_chat_id equals admin_group_id, the backup should be sent
        to the admin group and no extra confirmation message is sent.
        """
        admin_group_id = Config.post_get("admin_group_id")
        Config.override_settings({"debug": {"backup_chat_id": admin_group_id}})

        await db_backup_job(context=context_with_bot)

        mock_bot.send_document.assert_called_once()
        call_kwargs = mock_bot.send_document.call_args
        assert call_kwargs.kwargs["chat_id"] == admin_group_id
        assert call_kwargs.kwargs["caption"] == "✅ Backup effettuato con successo"
        assert call_kwargs.kwargs["filename"] == "spotted.backup.sqlite3"

        # No extra message since backup_chat_id == admin_group_id
        mock_bot.send_message.assert_not_called()

    @patch("spotted.handlers.job_handlers.get_backup", return_value=b"fake_db_content")
    async def test_backup_job_sends_to_different_chat(
        self, mock_get_backup, context_with_bot: CallbackContext, mock_bot: AsyncMock
    ):
        """When backup_chat_id is set to a valid chat different from admin_group_id,
        the backup should be sent to that chat and a confirmation to the admin group.
        """
        different_chat_id = -999
        Config.override_settings({"debug": {"backup_chat_id": different_chat_id}})

        await db_backup_job(context=context_with_bot)

        # Document sent to the specified backup chat
        mock_bot.send_document.assert_called_once()
        call_kwargs = mock_bot.send_document.call_args
        assert call_kwargs.kwargs["chat_id"] == different_chat_id

        # Confirmation message sent to the admin group
        admin_group_id = Config.post_get("admin_group_id")
        mock_bot.send_message.assert_called_once_with(chat_id=admin_group_id, text="✅ Backup effettuato con successo")

    @patch("spotted.handlers.job_handlers.get_backup", return_value=b"fake_db_content")
    async def test_backup_job_telegram_error_on_invalid_chat(
        self, mock_get_backup, context_with_bot: CallbackContext, mock_bot: AsyncMock
    ):
        """When backup_chat_id points to an invalid/unreachable chat,
        the TelegramError should be caught and an error message sent to the admin group.
        """
        invalid_chat_id = -12345
        Config.override_settings({"debug": {"backup_chat_id": invalid_chat_id}})
        mock_bot.send_document.side_effect = TelegramError("Chat not found")

        await db_backup_job(context=context_with_bot)

        # Should report the error to the admin group
        admin_group_id = Config.post_get("admin_group_id")
        mock_bot.send_message.assert_called_once_with(
            chat_id=admin_group_id,
            text="✖️ Impossibile inviare il backup\n\nChat not found",
        )

    @patch("spotted.handlers.job_handlers.get_zip_backup", return_value=b"fake_zip_content")
    async def test_backup_job_zip_to_different_chat(
        self, mock_get_zip, context_with_bot: CallbackContext, mock_bot: AsyncMock
    ):
        """When zip_backup is enabled and backup_chat_id is a different chat,
        the zip backup should be sent to that chat with the correct filename.
        """
        different_chat_id = -888
        Config.override_settings({"debug": {"backup_chat_id": different_chat_id, "zip_backup": True}})

        await db_backup_job(context=context_with_bot)

        mock_bot.send_document.assert_called_once()
        call_kwargs = mock_bot.send_document.call_args
        assert call_kwargs.kwargs["chat_id"] == different_chat_id
        assert call_kwargs.kwargs["filename"] == "spotted.backup.zip"

        # Confirmation sent to admin group
        admin_group_id = Config.post_get("admin_group_id")
        mock_bot.send_message.assert_called_once_with(chat_id=admin_group_id, text="✅ Backup effettuato con successo")

        # Reset zip_backup
        Config.override_settings({"debug": {"zip_backup": False}})

    @patch("spotted.handlers.job_handlers.get_zip_backup", return_value=b"fake_zip_content")
    async def test_backup_job_zip_to_admin_group(
        self, mock_get_zip, context_with_bot: CallbackContext, mock_bot: AsyncMock
    ):
        """When zip_backup is enabled and backup_chat_id equals admin_group_id,
        only the document is sent (no extra confirmation message).
        """
        admin_group_id = Config.post_get("admin_group_id")
        Config.override_settings({"debug": {"backup_chat_id": admin_group_id, "zip_backup": True}})

        await db_backup_job(context=context_with_bot)

        mock_bot.send_document.assert_called_once()
        call_kwargs = mock_bot.send_document.call_args
        assert call_kwargs.kwargs["chat_id"] == admin_group_id
        assert call_kwargs.kwargs["filename"] == "spotted.backup.zip"

        # No extra message since backup_chat_id == admin_group_id
        mock_bot.send_message.assert_not_called()

        # Reset zip_backup
        Config.override_settings({"debug": {"zip_backup": False}})
