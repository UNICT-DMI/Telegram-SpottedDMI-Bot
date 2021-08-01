# pylint: disable=unused-argument,protected-access,no-value-for-parameter
"""TelegramSimulator class"""
from datetime import datetime
from typing import List, Optional, Union
from telegram import Message, ReplyMarkup, MessageEntity, User, Chat, Update, CallbackQuery, update
from telegram.ext import Updater
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup
from main import add_handlers


class TelegramSimulator():
    """Weaves the standard bot class to intercept any contact with the telegram api and store the message"""
    __name = "BOT"
    __bot_id = 1234567890
    __current_id = 0
    __default_chat = Chat(id=1, type='private')
    __default_user = User(id=1, first_name='User', is_bot=False)
    __chat = __default_chat
    __user = __default_user

    def __init__(self):
        self.messages: List[Message] = []
        self.updater = Updater("1234567890:qY9gv7pRJgFj4EVmN3Z1gfJOgQpCbh0vmp5")
        add_handlers(self.updater.dispatcher)
        self.bot = self.updater.bot
        self.bot._bot = User(self.__bot_id, self.__name, is_bot=True, username=self.__name)
        self.bot._message = self.weaved_message().__get__(self.bot, self.bot.__class__)
        self.bot._post = self.weaved_post().__get__(self.bot, self.bot.__class__)
        self.bot.delete_webhook = self.weaved_delete_webhook().__get__(self.bot, self.bot.__class__)
        self.bot.copy_message = self.weaved_copy_message().__get__(self.bot, self.bot.__class__)

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

    def get_callback_query_data(self, text: str, message: Message) -> str:
        """Returs the data of the callback query from the inline button with the given text from the given message

        Args:
            text: text of the inline button
            message: message to extract the data from

        Returns:
            data of the callback query, or an empty string if no data was found
        """
        for inline_keyboard in message.reply_markup.inline_keyboard:
            for button in inline_keyboard:
                if button.text == text:
                    return button.callback_data
        return ""

    def send_command(self,
                     text: str = None,
                     message: Message = None,
                     user: User = None,
                     chat: Chat = None,
                     date: datetime = None,
                     reply_markup: InlineKeyboardMarkup = None,
                     **kwargs) -> Message:
        """Sends a command to the bot on behalf of the user

        Args:
            text: message text. Must be specified is message is None. Defaults to None
            message: message to send. Must be specified is text is None. Defaults to None
            user: user who sent the message. Defaults to None.
            chat: chat where the message was sent. Defaults to None.
            date: date when the message was sent. Defaults to None.
            reply_markup: reply markup to use. Defaults to None.
            **kwargs: additional parameters to be passed to the message. Defaults to None.

        Returns:
            message sent
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
                     **kwargs) -> Message:
        """Sends a message to the bot on behalf of the user

        Args:
            text: message text. Must be specified is message is None. Defaults to None
            message: message to send. Must be specified is text is None. Defaults to None
            user: user who sent the message. Defaults to None.
            chat: chat where the message was sent. Defaults to None.
            date: date when the message was sent. Defaults to None.
            reply_markup: reply markup to use. Defaults to None.
            **kwargs: additional parameters to be passed to the message. Defaults to None.

        Returns:
            message sent
        """
        if message is None:
            message = self.make_message(text=text, user=user, chat=chat, date=date, reply_markup=reply_markup, **kwargs)
        self.add_message(message)
        update = self.make_update(message)
        self.updater.dispatcher.process_update(update)
        return message

    def send_callback_query(self,
                            data: str = None,
                            message: Message = None,
                            text: str = None,
                            query: CallbackQuery = None,
                            user: User = None,
                            chat: Chat = None,
                            **kwargs) -> CallbackQuery:
        """Sends a callback query on an inline keyboard button to the bot on behalf of the user

        Args:
            data: data of the callback query. Must be specified is message is None. Defaults to None
            query: query to send. Must be specified is text is None. Defaults to None
            user: user who sent the message. Defaults to None.
            chat: chat where the message was sent. Defaults to None.
            message: message the callback query belongs to. Defaults to None.
            **kwargs: additional parameters to be passed to the message. Defaults to None.

        Returns:
            callback query answered
        """
        message = message if message is not None else self.last_message
        if data is None and text is not None:
            data = self.get_callback_query_data(text, message)
        if query is None:
            query = self.make_callback_query(user=user, chat=chat, data=data, message=message, **kwargs)
        update = self.make_update(query)
        self.updater.dispatcher.process_update(update)
        return query

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

    def make_callback_query(self,
                            message: Message,
                            user: User = None,
                            chat: Chat = None,
                            data: str = None,
                            **kwargs) -> Message:
        """Creates a telegram message from the given parameters

        Args:
            text: message text
            user: user who sent the message. Defaults to None.
            chat: chat where the message was sent. Defaults to None.
            data: data contained in the callback query. Defaults to None.
            message: message the callback query belongs to. Defaults to None.
            **kwargs: additional parameters to be passed to the message. Defaults to None.

        Returns:
            message created from the given parameters
        """
        return CallbackQuery(id=0,
                             from_user=user if user is not None else self.user,
                             chat_instance=str(chat.id) if chat is not None else str(self.chat.id),
                             message=message,
                             data=data,
                             **kwargs)

    def make_update(self, event: Union[CallbackQuery, Message], edited: bool = False, **kwargs):
        """Testing utility factory to create an update from a user event, as either a
        :class:`Message`` or a :class:`CallbackQuery` from an inline keyboard

        Args:
            message: either a :class:`Message` or a :class:`CallbackQuery` from an inline keyboard
            edited: whether the message should be stored as an edited message

        Returns:
            update with the given message
        """
        if isinstance(event, Message):
            update_kwargs = {'message' if not edited else 'edited_message': event}
        elif isinstance(event, CallbackQuery):
            update_kwargs = {'callback_query': event}
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
            message.chat = Chat(id=data['chat_id'], type="")

            self.add_message(message)
            return message

        return _message

    def weaved_delete_webhook(self):
        """Weaves the delete_webhook method in the bot object to intercept telegram's api requests"""
        return lambda *_, **__: True

    def weaved_post(self):
        """Weaves the post method in the bot object to intercept telegram's api requests"""
        return lambda *_, **__: []

    def weaved_copy_message(self):
        """Weaves the post method in the bot object to intercept telegram's api requests"""

        def copy_message(bot_self, chat_id: Union[int, str], from_chat_id: Union[str, int], message_id: Union[str, int], *args,
                         **kwargs) -> int:
            message_to_copy: Optional[Message] = next(
                filter(lambda message: message.message_id == message_id and message.chat_id == from_chat_id, self.messages),
                None)
            chat = Chat(id=chat_id, type='')
            message = self.make_message(text=message_to_copy.text, reply_markup=message_to_copy.reply_markup, chat=chat)
            return message

        return copy_message

    def add_message(self, message: Message):
        """Adds a message to the list of messages

        Args:
            message: message to add
        """
        self.messages.append(message)
