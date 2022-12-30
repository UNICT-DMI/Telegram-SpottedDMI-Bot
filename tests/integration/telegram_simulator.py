# pylint: disable=unused-argument,protected-access,no-value-for-parameter
"""TelegramSimulator class"""
from datetime import datetime
from typing import List, Optional, Union
import warnings
from telegram import Message, ReplyMarkup, MessageEntity, User, Chat, Update, CallbackQuery, InlineKeyboardButton
from telegram.ext import Updater
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup
from main import add_handlers


class TelegramSimulator():
    """Weaves the standard bot class to intercept any contact with the telegram api and store the message"""
    __name = "BOT"
    __bot_id = 1234567890
    __current_id = 200
    __default_chat = Chat(id=1, type='private')
    __default_user = User(id=1, first_name='User', username="Username", is_bot=False)
    __chat = __default_chat
    __user = __default_user

    def __init__(self):
        warnings.filterwarnings("ignore", message=r"Setting custom attributes such as .*")
        self.messages: List[Message] = []
        self.updater = Updater("1234567890:qY9gv7pRJgFj4EVmN3Z1gfJOgQpCbh0vmp5")
        add_handlers(self.updater.dispatcher)
        for group in self.updater.dispatcher.groups:
            for handler in self.updater.dispatcher.handlers[group]:
                handler.run_async = False
        self.bot = self.updater.bot
        self.bot._bot = User(self.__bot_id, self.__name, is_bot=True, username=self.__name)
        self.bot._message = self.weaved_message().__get__(self.bot, self.bot.__class__)
        self.bot._post = self.weaved_post().__get__(self.bot, self.bot.__class__)
        self.bot.delete_webhook = self.weaved_delete_webhook().__get__(self.bot, self.bot.__class__)
        self.bot.copy_message = self.weaved_copy_message().__get__(self.bot, self.bot.__class__)
        self.bot.get_chat = self.weaved_get_chat().__get__(self.bot, self.bot.__class__)

    @property
    def current_id(self) -> int:
        """Returns the current message id and increases it by one"""
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
        """Returns the data of the callback query from the inline button with the given text from the given message

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
            text: message text. Must be specified is message is None
            message: message to send. Must be specified is text is None
            user: user who sent the message
            chat: chat where the message was sent
            date: date when the message was sent
            reply_markup: reply markup to use
            **kwargs: additional parameters to be passed to the message

        Returns:
            message sent
        """
        if message is None:
            message = self.make_message(text=text, user=user, chat=chat, date=date, reply_markup=reply_markup, **kwargs)
            command_len = len(text.split(" ")[0])
            message.entities.append(MessageEntity(type=MessageEntity.BOT_COMMAND, offset=0, length=command_len))
        self.send_message(message=message)

    def send_message(self,
                     text: str = None,
                     message: Message = None,
                     user: User = None,
                     chat: Chat = None,
                     date: datetime = None,
                     reply_markup: InlineKeyboardMarkup = None,
                     reply_to_message: Union[Message, int] = None,
                     entities: List[MessageEntity] = None,
                     **kwargs) -> Message:
        """Sends a message to the bot on behalf of the user

        Args:
            text: message text. Must be specified is message is None
            message: message to send. Must be specified is text is None
            user: user who sent the message
            chat: chat where the message was sent
            date: date when the message was sent
            reply_markup: reply markup to use
            reply_to_message: message (or message_id of said message) to reply to
            entities: list of entities to use in the message
            **kwargs: additional parameters to be passed to the message

        Returns:
            message sent
        """
        if message is None:
            message = self.make_message(text=text,
                                        user=user,
                                        chat=chat,
                                        date=date,
                                        reply_markup=reply_markup,
                                        reply_to_message=reply_to_message,
                                        entities=entities,
                                        **kwargs)
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
            data: data of the callback query. Must be specified is message is None
            query: query to send. Must be specified is text is None
            user: user who sent the message
            chat: chat where the message was sent
            message: message the callback query belongs to
            **kwargs: additional parameters to be passed to the message

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

    def send_forward_message(self,
                             forward_message: Message = None,
                             message: Message = None,
                             user: User = None,
                             chat: Chat = None,
                             date: datetime = None,
                             reply_markup: InlineKeyboardMarkup = None,
                             reply_to_message: Union[Message, int] = None,
                             is_automatic_forward: bool = False,
                             **kwargs) -> Message:
        """Sends a message to the bot on behalf of the user

        Args:
            forward_message: message to forward. Must be specified is message is None
            message: message to send. Must be specified is text is None
            user: user who sent the message
            chat: chat where the message was sent
            date: date when the message was sent
            reply_markup: reply markup to use
            reply_to_message: message (or message_id of said message) to reply to
            is_automatic_forward: whether the message was forwarded automatically by telegram
            **kwargs: additional parameters to be passed to the message

        Returns:
            message sent
        """
        if message is None:
            message = self.make_message(text=forward_message.text,
                                        forward_from_chat=forward_message.chat,
                                        forward_from=forward_message.from_user,
                                        forward_message=forward_message,
                                        forward_from_message_id=forward_message.message_id,
                                        forward_date=forward_message.date,
                                        user=user,
                                        chat=chat,
                                        date=date,
                                        reply_markup=reply_markup,
                                        reply_to_message=reply_to_message,
                                        **kwargs)
            message.is_automatic_forward = is_automatic_forward
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
                     reply_to_message: Union[Message, int] = None,
                     **kwargs) -> Message:
        """Creates a telegram message from the given parameters

        Args:
            text: message text
            user: user who sent the message
            chat: chat where the message was sent
            date: date when the message was sent
            reply_markup: reply markup to use
            reply_to_message: message (or message_id of said message) to reply to
            **kwargs: additional parameters to be passed to the message

        Returns:
            message created from the given parameters
        """
        if isinstance(reply_to_message, int):
            reply_to_message = self.get_message_with_id(reply_to_message)
        return Message(message_id=self.current_id,
                       from_user=user if user is not None else self.user,
                       date=date if date is not None else datetime.now(),
                       chat=chat if chat is not None else self.chat,
                       text=text,
                       bot=self.bot,
                       reply_markup=reply_markup,
                       reply_to_message=reply_to_message,
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
            user: user who sent the message
            chat: chat where the message was sent
            data: data contained in the callback query
            message: message the callback query belongs to
            **kwargs: additional parameters to be passed to the message

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
        """Weaves the _message method in the bot object to intercept telegram's api requests

        Returns:
            weaved bot's _message method
        """

        def _message(bot_self,
                     endpoint: str,
                     data: dict,
                     reply_to_message_id: int = None,
                     disable_notification: bool = None,
                     reply_markup: ReplyMarkup = None,
                     allow_sending_without_reply: bool = None,
                     timeout: float = None,
                     api_kwargs: dict = None,
                     protect_content: bool = None) -> Union[bool, Message]:
            data.update({'message_id': self.current_id, 'date': datetime.now().timestamp()})

            message = Message.de_json(data, bot_self)
            if reply_to_message_id is not None:
                if isinstance(reply_to_message_id, int):
                    message.reply_to_message = self.get_message_with_id(reply_to_message_id)
                else:
                    message.reply_to_message = reply_to_message_id
            message.reply_markup = reply_markup
            message.from_user = bot_self._bot
            message.chat = Chat(id=data['chat_id'], type="")

            self.add_message(message)
            return message

        return _message

    def weaved_delete_webhook(self):
        """Weaves the delete_webhook method in the bot object to intercept telegram's api requests

        Returns:
            weaved bot's delete_webhook method
        """
        return lambda *_, **__: True

    def weaved_post(self):
        """Weaves the _post method in the bot object to intercept telegram's api requests

        Returns:
            weaved bot's _post method
        """

        def _post(bot_self,
                  endpoint: str,
                  data: dict = None,
                  timeout: float = None,
                  api_kwargs: dict = None) -> Union[bool, dict, None]:
            if endpoint == "deleteMessage":
                self.messages = [m for m in self.messages if m.message_id != data['message_id']]

            return True

        return _post

    def weaved_copy_message(self):
        """Weaves the copy_message method in the bot object to intercept telegram's api requests

        Returns:
            weaved bot's copy_message method
        """

        def copy_message(bot_self,
                         chat_id: Union[int, str],
                         from_chat_id: Union[str, int],
                         message_id: Union[str, int],
                         *args,
                         reply_markup: ReplyMarkup = None,
                         **kwargs) -> int:
            message_to_copy: Optional[Message] = next(
                filter(lambda message: message.message_id == message_id and message.chat_id == from_chat_id, self.messages),
                None)
            chat = Chat(id=chat_id, type='')
            message = self.make_message(
                text=message_to_copy.text,
                reply_markup=reply_markup if reply_markup is not None else message_to_copy.reply_markup,
                chat=chat,
                user=bot_self._bot)

            self.add_message(message)
            return message

        return copy_message

    def weaved_get_chat(self):
        """Weaves the get_chat method in the bot object to intercept telegram's api requests

        Returns:
            weaved bot's get_chat method
        """

        def get_chat(
            self,
            chat_id: Union[str, int],
            timeout: float = None,
            api_kwargs: dict = None,
        ) -> Chat:
            str_chat_id = str(chat_id)
            return Chat(id=chat_id, type=Chat.PRIVATE, username=str_chat_id, first_name=str_chat_id,
                        last_name=str_chat_id)  # type: ignore

        return get_chat

    def add_message(self, message: Message):
        """Adds a message to the list of messages

        Args:
            message: message to add
        """
        self.messages.append(message)

    def find_button_on_keyboard(self, text: str, message: Message) -> Optional[InlineKeyboardButton]:
        """Find a button on the keyboard with the given text

        Args:
            text: text of the button to find
            message: message containing the keyboard

        Returns:
            the button found or None
        """
        for row in message.reply_markup.inline_keyboard:
            for button in row:
                if button.text == text:
                    return button
        return None
