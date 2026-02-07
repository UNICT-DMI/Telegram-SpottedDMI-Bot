# pylint: disable=redefined-outer-name
"""Shared fixtures for unit tests"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from telegram.ext import Application, CallbackContext

from spotted.data import Config
from spotted.utils import EventInfo


@pytest.fixture(scope="function")
def mock_bot() -> AsyncMock:
    """Create a mock bot instance"""
    bot = AsyncMock()
    bot.send_message = AsyncMock(return_value=None)
    bot.restrict_chat_member = AsyncMock(return_value=None)
    bot.get_chat_administrators = AsyncMock(
        return_value=[
            MagicMock(user=MagicMock(id=999)),  # Admin user
        ]
    )
    return bot


@pytest.fixture(scope="function")
def context_with_bot(mock_bot: AsyncMock) -> CallbackContext:
    """Return a CallbackContext with a mocked bot"""
    app = Application.builder().token("1234567890:qY9gv7pRJgFj4EVmN3Z1gfJOgQpCbh0vmp5").build()
    app.bot = mock_bot
    context = CallbackContext(app)
    return context


@pytest.fixture(scope="function")
def mock_event_info(mock_bot: AsyncMock, context_with_bot: CallbackContext) -> EventInfo:
    """Create a mock EventInfo instance"""
    info = MagicMock(spec=EventInfo)
    info.bot = mock_bot
    info.context = context_with_bot
    info.chat_id = Config.post_get("admin_group_id")
    info.user_id = 999  # Admin user
    info.message = MagicMock()
    return info
