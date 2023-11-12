# pylint: disable=unused-argument,protected-access,no-value-for-parameter
"""TelegramSimulator class"""
import warnings
from datetime import datetime
from typing import overload

from telegram import (
    CallbackQuery,
    Chat,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    MessageEntity,
    Update,
    User,
)
from telegram.ext import Application
from telegram_api import TelegramApi

from spotted.handlers import add_handlers


class TelegramSimulator:  # pylint: disable=too-many-public-methods
    """Weaves the standard bot class to intercept any contact with the telegram api and store the message"""

    __default_chat = Chat(id=1, type="private")
    __default_user = User(id=1, first_name="User", username="Username", is_bot=False)
    __chat = __default_chat
    __user = __default_user

    def __init__(self):
        warnings.filterwarnings("ignore", message=r"Setting custom attributes such as .*")
        self.messages: list[Message] = []
        self.app = Application.builder().token("1234567890:qY9gv7pRJgFj4EVmN3Z1gfJOgQpCbh0vmp5").build()
        add_handlers(self.app)
        self.bot = self.app.bot
        self.bot._post = self.weaved_post().__get__(self.bot, self.bot.__class__)
        self.__api = TelegramApi(self)

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
        self.__chat = self.__default_chat
        self.__user = self.__default_user

    def get_message_by_id(self, message_id: int | str) -> Message | None:
        """Return the first message with the given message id or None if no message with this id was found

        Args:
            message_id: message id to search for

        Returns:
            message with the given message id
        """
        if isinstance(message_id, str):
            message_id = int(message_id)
        return next(filter(lambda message: message.message_id == message_id, self.messages), None)

    def edit_message(self, edited_message: Message):
        """Updates the message with the given message id with the given dict

        Args:
            message: message to update
        """
        self.messages = [
            message if message.message_id != edited_message.message_id else edited_message for message in self.messages
        ]

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

    @overload
    async def send_command(
        self,
        text: "str",
        user: "User" = None,
        chat: "Chat" = None,
        reply_to_message: "Message | int | None" = None,
    ) -> "Message":
        ...

    async def send_command(
        self,
        text: "str" = None,
        entities: "list[MessageEntity] | None" = None,
        **kwargs,
    ) -> "Message":
        """Sends a command to the bot on behalf of the user

        Args:
            text: message text. Must be specified is message is None
            message: message to send. Must be specified is text is None
            entities: list of entities to use in the message. Automatically adds a bot command entity
            **kwargs: additional parameters to be passed to the message

        Returns:
            message sent
        """
        command_len = len(text.split(" ")[0])
        command = MessageEntity(type=MessageEntity.BOT_COMMAND, offset=0, length=command_len)
        entities = entities if entities is not None else []
        entities.append(command)
        return await self.send_message(text=text, entities=entities, **kwargs)

    @overload
    async def send_message(
        self,
        text: "str",
        user: "User" = None,
        chat: "Chat" = None,
        entities: "list[MessageEntity] | None" = None,
        reply_to_message: "Message | int | None" = None,
        message_thread_id: "int | None" = None,
    ) -> "Message":
        ...

    @overload
    async def send_message(self, message: "Message") -> "Message":
        ...

    async def send_message(
        self,
        text: str = None,
        message: Message = None,
        **kwargs,
    ) -> Message:
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
            message = self.make_message(
                text=text,
                **kwargs,
            )
        self.add_message(message)
        update = self.make_update(message)
        await self.app.initialize()
        await self.app.process_update(update)
        return message

    async def send_callback_query(
        self,
        data: str = None,
        message: Message = None,
        text: str = None,
        query: CallbackQuery = None,
        user: User = None,
        chat: Chat = None,
        **kwargs,
    ) -> CallbackQuery:
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
        await self.app.initialize()
        await self.app.process_update(update)
        return query

    async def send_forward_message(
        self,
        forward_message: "int | Message" = None,
        message: Message = None,
        user: User = None,
        chat: Chat = None,
        date: datetime = None,
        reply_markup: InlineKeyboardMarkup = None,
        reply_to_message: Message | int = None,
        is_automatic_forward: bool = False,
        **kwargs,
    ) -> Message:
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
        if isinstance(forward_message, int):
            forward_message = self.get_message_by_id(forward_message)
        if message is None:
            message = self.make_message(
                text=forward_message.text,
                forward_from_chat=forward_message.chat,
                forward_from=forward_message.from_user,
                forward_from_message_id=forward_message.message_id,
                forward_date=forward_message.date,
                user=user,
                chat=chat,
                date=date,
                reply_markup=reply_markup,
                reply_to_message=reply_to_message,
                is_automatic_forward=is_automatic_forward,
                **kwargs,
            )
        self.add_message(message)
        update = self.make_update(message)
        await self.app.initialize()
        await self.app.process_update(update)
        return message

    def make_message(
        self,
        text: str,
        user: User = None,
        chat: Chat = None,
        date: datetime = None,
        reply_markup: InlineKeyboardMarkup = None,
        reply_to_message: Message | int = None,
        entities: list[MessageEntity] = None,
        **kwargs,
    ) -> Message:
        """Creates a telegram message from the given parameters

        Args:
            text: message text
            user: user who sent the message
            chat: chat where the message was sent
            date: date when the message was sent
            reply_markup: reply markup to use
            reply_to_message: message (or message_id of said message) to reply to
            entities: list of entities to use in the message
            **kwargs: additional parameters to be passed to the message

        Returns:
            message created from the given parameters
        """
        if isinstance(reply_to_message, int):
            reply_to_message = self.get_message_by_id(reply_to_message)
        message = Message(
            message_id=self.__api.get_next_id(),
            from_user=user if user is not None else self.user,
            date=date if date is not None else datetime.now(),
            chat=chat if chat is not None else self.chat,
            text=text,
            reply_markup=reply_markup,
            reply_to_message=reply_to_message,
            entities=entities,
            **kwargs,
        )
        message.set_bot(self.bot)
        return message

    def make_callback_query(
        self, message: Message, user: User = None, chat: Chat = None, data: str = None, **kwargs
    ) -> Message:
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
        return CallbackQuery(
            id=0,
            from_user=user if user is not None else self.user,
            chat_instance=str(chat.id) if chat is not None else str(self.chat.id),
            message=message,
            data=data,
            **kwargs,
        )

    def make_update(self, event: CallbackQuery | Message, edited: bool = False, **kwargs):
        """Testing utility factory to create an update from a user event, as either a
        :class:`Message`` or a :class:`CallbackQuery` from an inline keyboard

        Args:
            message: either a :class:`Message` or a :class:`CallbackQuery` from an inline keyboard
            edited: whether the message should be stored as an edited message

        Returns:
            update with the given message
        """
        if isinstance(event, Message):
            update_kwargs = {"message" if not edited else "edited_message": event}
        elif isinstance(event, CallbackQuery):
            update_kwargs = {"callback_query": event}
        return Update(0, **update_kwargs)

    def weaved_post(self):
        """Weaves the _post method in the bot object to intercept telegram's api requests

        Returns:
            weaved bot's _post method
        """

        async def _post(
            bot_self,
            endpoint: str,
            data: dict = None,
            *,
            read_timeout: float = None,
            write_timeout: float = None,
            connect_timeout: float = None,
            pool_timeout: float = None,
            api_kwargs: dict = None,
        ) -> bool | dict | None:
            return self.__api.post(endpoint, data)

        return _post

    def add_message(self, message: Message):
        """Adds a message to the list of messages

        Args:
            message: message to add
        """
        self.messages.append(message)

    def delete_messaegge(self, message: int | Message):
        """Removes a message from the list of messages

        Args:
            message: message to remove or its message id
        """
        if isinstance(message, int):
            message = self.get_message_by_id(message)
            self.messages.remove(message)
        else:
            self.messages.remove(message)

    def find_button_on_keyboard(self, text: str, message: Message) -> InlineKeyboardButton | None:
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
