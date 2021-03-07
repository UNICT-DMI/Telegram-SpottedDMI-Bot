"""Common info needed in both command and callback handlers"""
from telegram import Bot, Update, Message, CallbackQuery, ReplyMarkup, Chat
from telegram.ext import CallbackContext
from telegram.error import BadRequest
from modules.debug.log_manager import logger


class EventInfo():
    """Class that contains all the relevant information related to an event
    """

    def __init__(self,
                 bot: Bot,
                 ctx: CallbackContext,
                 update: Update = None,
                 message: Message = None,
                 query: CallbackQuery = None):
        self.__bot = bot
        self.__ctx = ctx
        self.__update = update
        self.__message = message
        self.__query = query

    @property
    def bot(self) -> Bot:
        """Istance of the telegram bot"""
        return self.__bot

    @property
    def context(self) -> CallbackContext:
        """Context generated by some event"""
        return self.__ctx

    @property
    def update(self) -> Update:
        """Update generated by some event. Defaults to None"""
        return self.__update

    @property
    def message(self) -> Message:
        """Message that caused the update. Defaults to None"""
        return self.__message

    @property
    def bot_data(self) -> dict:
        """Data related to the bot. Is not persistent between restarts"""
        return self.__ctx.bot_data

    @property
    def user_data(self) -> dict:
        """Data related to the user. Is not persistent between restarts"""
        return self.__ctx.user_data

    @property
    def chat_id(self) -> int:
        """Id of the chat where the event happened. Defaults to None"""
        if self.__message is None:
            return None
        return self.__message.chat_id

    @property
    def chat_type(self) -> str:
        """Type of the chat where the event happened. Defaults to None"""
        if self.__message is None:
            return None
        return self.__message.chat.type

    @property
    def is_private_chat(self) -> bool:
        """Checks that the chat is private

        Returns:
            bool: whether the chat is private or not
        """
        if self.chat_type is None:
            return None
        return self.chat_type == Chat.PRIVATE

    @property
    def text(self) -> str:
        """Text of the message that caused the update. Defaults to None"""
        if self.__message is None:
            return None
        return self.__message.text

    @property
    def message_id(self) -> int:
        """Id of the message that caused the update. Defaults to None"""
        if self.__message is None:
            return None
        return self.__message.message_id

    @property
    def is_valid_message_type(self) -> bool:
        """Checks that the type of the message is among the ones supported

        Returns:
            bool: whether its type is supported or not
        """
        if self.__message is None:
            return None
        return self.__message.text or self.__message.photo or self.__message.voice or self.__message.audio\
        or self.__message.video or self.__message.animation or self.__message.sticker or self.__message.poll

    @property
    def reply_markup(self) -> ReplyMarkup:
        """Reply_markup of the message that caused the update. Defaults to None"""
        if self.__message is None:
            return None
        return self.__message.reply_markup

    @property
    def user_id(self) -> int:
        """Id of the user that caused the update. Defaults to None"""
        if self.__query is not None:
            return self.__query.from_user.id
        if self.__message is not None:
            return self.__message.from_user.id
        return None

    @property
    def user_username(self) -> int:
        """Username of the user that caused the update. Defaults to None"""
        if self.__query is not None:
            return self.__query.from_user.username
        if self.__message is not None:
            return self.__message.from_user.username
        return None

    @property
    def query_id(self) -> int:
        """Id of the query that caused the update. Defaults to None"""
        if self.__query is None:
            return None
        return self.__query.id

    @property
    def query_data(self) -> str:
        """Data associated with the query that caused the update. Defaults to None"""
        if self.__query is None:
            return None
        return self.__query.data

    @classmethod
    def from_message(cls, update: Update, ctx: CallbackContext):
        """Istance of SpottedBot created by a message update"""
        return cls(bot=ctx.bot, ctx=ctx, update=update, message=update.message)

    @classmethod
    def from_callback(cls, update: Update, ctx: CallbackContext):
        """Istance of SpottedBot created by a callback update"""
        return cls(bot=ctx.bot, ctx=ctx, update=update, message=update.callback_query.message, query=update.callback_query)

    @classmethod
    def from_job(cls, ctx: CallbackContext):
        """Istance of SpottedBot created by a job update"""
        return cls(bot=ctx.bot, ctx=ctx)

    def answer_callback_query(self, text: str = None):
        """Calls the answer_callback_query method of the bot class, while also handling the exception

        Args:
            text (str, optional): Text to show to the user. Defaults to None.
        """
        try:
            self.__bot.answer_callback_query(callback_query_id=self.query_id, text=text)
        except BadRequest as e:
            logger.warning("On answer_callback_query: %s", e)
