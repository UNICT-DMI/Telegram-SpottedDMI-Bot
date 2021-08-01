# pylint: disable=unused-argument,protected-access,no-value-for-parameter
"""TelegramSimulator class"""
from datetime import datetime
from typing import Callable, List, Optional, Union
from telegram import Message, ReplyMarkup, MessageEntity, User, Chat, Update
from telegram.ext import Updater
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup
from modules.utils import Singleton


class TelegramSimulator(metaclass=Singleton):
    """Weaves the standard bot class to intercept any contact with the telegram api and store the message"""
    __name = "BOT"
    __bot_id = 1234567890
    __current_id = 0
    __default_chat = Chat(id=1, type='')
    __default_user = User(id=1, first_name='User', is_bot=False)
    __chat = __default_chat
    __user = __default_user

    def __init__(self, updater: Updater):
        self.messages: List[Message] = []
        self.updater = updater
        self.bot = updater.bot
        self.bot._bot = User(self.__bot_id, self.__name, is_bot=True, username=self.__name)
        self.bot._message = self.weaved_message().__get__(self.bot, self.bot.__class__)
        self.bot._post = self.weaved_post().__get__(self.bot, self.bot.__class__)
        self.bot.delete_webhook = self.weaved_delete_webhook().__get__(self.bot, self.bot.__class__)

    @property
    def current_id(self) -> int:
        """Returns the current message id and increses it by one"""
        self.__current_id += 1
        return self.__current_id

    @property
    def last_message(self) -> Message:
        """Last message registered"""
        return self.messages[-1]

    @property
    def chat(self) -> Chat:
        """Placeholder chat used in every operation"""
        return self.__chat

    @chat.setter
    def chat(self, chat: Chat):
        self.__chat = chat

    @property
    def user(self) -> User:
        """Placeholder user used in every operation"""
        return self.__user

    @user.setter
    def user(self, user: User):
        self.__user = user

    def reset(self):
        """Resets the telegram wrapper values"""
        self.messages = []
        self.__current_id = 0
        self.__chat = self.__default_chat
        self.__user = self.__default_user

    def get_message_with_id(self, message_id: int) -> Optional[Message]:
        """Return the first message with the given message id or None if no message with this id was found

        Args:
            message_id: message id to search for

        Returns:
            message with the given message id
        """
        return next(filter(lambda message: message.message_id == message_id, self.messages), None)

    def send_command(self,
                     text: str = None,
                     message: Message = None,
                     user: User = None,
                     chat: Chat = None,
                     date: datetime = None,
                     reply_markup: InlineKeyboardMarkup = None,
                     **kwargs):
        """Sends a command to the bot on behalf of the user

        Args:
            text: message text. Must be specified is message is None. Defaults to None
            message: message to send. Must be specified is text is None. Defaults to None
            user: user who sent the message. Defaults to None.
            chat: chat where the message was sent. Defaults to None.
            date: date when the message was sent. Defaults to None.
            reply_markup: reply markup to use. Defaults to None.
            **kwargs: additional parameters to be passed to the message. Defaults to None.
        """
        if message is None:
            message = self.make_message(text=text, user=user, chat=chat, date=date, reply_markup=reply_markup, **kwargs)
            message.entities.append(MessageEntity(type=MessageEntity.BOT_COMMAND, offset=0, length=len(text)))
        self.send_message(message=message)

    def send_message(self,
                     text: str = None,
                     message: Message = None,
                     user: User = None,
                     chat: Chat = None,
                     date: datetime = None,
                     reply_markup: InlineKeyboardMarkup = None,
                     **kwargs):
        """Sends a message to the bot on behalf of the user

        Args:
            text: message text. Must be specified is message is None. Defaults to None
            message: message to send. Must be specified is text is None. Defaults to None
            user: user who sent the message. Defaults to None.
            chat: chat where the message was sent. Defaults to None.
            date: date when the message was sent. Defaults to None.
            reply_markup: reply markup to use. Defaults to None.
            **kwargs: additional parameters to be passed to the message. Defaults to None.
        """
        if message is None:
            message = self.make_message(text=text, user=user, chat=chat, date=date, reply_markup=reply_markup, **kwargs)
        self.add_message(message)
        update = self.make_update(message)
        self.updater.dispatcher.process_update(update)
        return message

    def make_message(self,
                     text: str,
                     user: User = None,
                     chat: Chat = None,
                     date: datetime = None,
                     reply_markup: InlineKeyboardMarkup = None,
                     **kwargs) -> Message:
        """Creates a telegram message from the given parameters

        Args:
            text: message text
            user: user who sent the message. Defaults to None.
            chat: chat where the message was sent. Defaults to None.
            date: date when the message was sent. Defaults to None.
            reply_markup: reply markup to use. Defaults to None.
            **kwargs: additional parameters to be passed to the message. Defaults to None.

        Returns:
            message created from the given parameters
        """
        return Message(message_id=self.current_id,
                       from_user=user if user is not None else self.user,
                       date=date if date is not None else datetime.now(),
                       chat=chat if chat is not None else self.chat,
                       text=text,
                       bot=self.bot,
                       reply_markup=reply_markup,
                       **kwargs)

    def make_update(self, message: Union[str, Message], message_factory: Callable = None, edited: bool = False, **kwargs):
        """Testing utility factory to create an update from a message, as either a
        ``telegram.Message`` or a string. In the latter case ``message_factory``
        is used to convert ``message`` to a ``telegram.Message``

        Args:
            message: either a ``telegram.Message`` or a string with the message text
            message_factory: function to convert the message text into a ``telegram.Message``
            edited: whether the message should be stored as ``edited_message`` (vs. ``message``)

        Returns:
            update with the given message
        """
        if message_factory is None:
            message_factory = self.make_message
        if not isinstance(message, Message):
            message = message_factory(message, **kwargs)
        update_kwargs = {'message' if not edited else 'edited_message': message}
        return Update(0, **update_kwargs)

    def weaved_message(self):
        """Weaves the _message method in the bot object to intercept telegram's api requests"""

        def _message(bot_self,
                     endpoint: str,
                     data: dict,
                     reply_to_message_id: int = None,
                     disable_notification: bool = None,
                     reply_markup: ReplyMarkup = None,
                     allow_sending_without_reply: bool = None,
                     timeout: float = None,
                     api_kwargs: dict = None) -> Union[bool, Message]:
            data.update({'message_id': self.current_id, 'date': datetime.now().timestamp()})

            message = Message.de_json(data, bot_self)
            message.reply_to_message = self.get_message_with_id(
                reply_to_message_id) if reply_to_message_id is not None else None
            message.reply_markup = reply_markup
            message.from_user = bot_self._bot

            self.add_message(message)
            return message

        return _message

    def weaved_delete_webhook(self):
        """Weaves the delete_webhook method in the bot object to intercept telegram's api requests"""
        return lambda *_, **__: True

    def weaved_post(self):
        """Weaves the post method in the bot object to intercept telegram's api requests"""
        return lambda *_, **__: []

    def add_message(self, message: Message):
        """Adds a message to the list of messages

        Args:
            message: message to add
        """
        self.messages.append(message)
