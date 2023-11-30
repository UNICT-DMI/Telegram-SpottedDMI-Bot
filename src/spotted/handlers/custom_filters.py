"""Defines custom filters to use for commands"""
from telegram import Chat, Message
from telegram.ext.filters import MessageFilter


class IsAdminFilter(MessageFilter):
    """Check if the message from the update was sent by
        one of the administrators of the group
    Args:
        MessageFilter: the superclass for the filter
    """

    def filter(self, message: Message):
        chat = message.chat
        sender_id = message.from_user.id
        if chat.type in [Chat.SUPERGROUP, Chat.GROUP]:
            return sender_id in [admin.id for admin in chat.get_administrators(chat.id)]
        return False
