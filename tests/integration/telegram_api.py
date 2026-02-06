# pylint: disable=unused-argument,protected-access,no-value-for-parameter,missing-function-docstring,missing-class-docstring,too-few-public-methods,too-many-arguments,too-many-locals,too-many-branches,too-many-statements,too-many-instance-attributes,too-many-public-methods,too-many-lines,too-many-nested-blocks,too-many-boolean-expressions,too-many-ancestors,too-many-function-args,too-many-locals,too-many-arguments,too-many-branches,too-many-statements,too-many-instance-attributes,too-many-public-methods,too-many-lines,too-many-nested-blocks,too-many-boolean-expressions,too-many-ancestors,too-many-function-args
"""TelegramApi class"""

from datetime import datetime
from typing import TYPE_CHECKING

from telegram import (
    AcceptedGiftTypes,
    Chat,
    ChatFullInfo,
    InlineKeyboardMarkup,
    LinkPreviewOptions,
    Message,
    MessageEntity,
    MessageOriginChannel,
    MessageOriginChat,
    MessageOriginUser,
    ReplyKeyboardMarkup,
    User,
)

from spotted.data import Config
from spotted.data import User as SpottedUser

if TYPE_CHECKING:
    from typing import TypedDict

    from telegram.constants import ParseMode

    from .telegram_simulator import TelegramSimulator

    class MessageData(TypedDict):
        chat_id: int
        text: str
        message_id: int
        entities: list[MessageEntity] | None
        disable_notification: bool | None
        allow_sending_without_reply: bool | None
        protect_content: bool | None
        parse_mode: ParseMode | None
        link_preview_options: LinkPreviewOptions | None
        reply_markup: ReplyKeyboardMarkup | InlineKeyboardMarkup | None


class TelegramApi:
    __current_id = 200

    def __init__(self, simulator: "TelegramSimulator"):
        self.__simulator = simulator
        self.__bot = self.__simulator.bot
        self.__chats: dict[int, Chat] = {}
        self.__chats[Config.post_get("admin_group_id")] = Chat(id=Config.post_get("admin_group_id"), type=Chat.GROUP)
        self.__chats[Config.post_get("channel_id")] = Chat(id=Config.post_get("channel_id"), type=Chat.CHANNEL)
        self.__chats[Config.post_get("community_group_id")] = Chat(
            id=Config.post_get("community_group_id"), type=Chat.GROUP
        )

    def get_forward_origin(
        self, forward_message: int | Message
    ) -> MessageOriginChannel | MessageOriginChat | MessageOriginUser:
        if isinstance(forward_message, int):
            forward_message = self.__simulator.get_message_by_id(forward_message)
        if forward_message.chat.type == Chat.PRIVATE:
            return MessageOriginUser(datetime.now(), forward_message.from_user.id)
        if forward_message.chat.type == Chat.CHANNEL:
            return MessageOriginChannel(
                datetime.now(),
                Chat(forward_message.chat.id, Chat.CHANNEL, "channel"),
                forward_message.id,
                forward_message.author_signature,
            )
        if forward_message.chat.type == Chat.GROUP:
            return MessageOriginChat(
                datetime.now(), Chat(forward_message.chat.id, Chat.GROUP, "group"), forward_message.author_signature
            )
        return None

    @classmethod
    def get_next_id(cls) -> int:
        """Returns the current message id and increases it by one"""
        cls.__current_id += 1
        return cls.__current_id

    def post(self, endpoint: str, data: dict) -> dict | bool | None:
        if endpoint == "getMe":
            return self.__get_me()
        if endpoint == "sendMessage":
            return self.__send_message(data)
        if endpoint == "editMessageText":
            return self.__edit_message(data)
        if endpoint == "editMessageReplyMarkup":
            return self.__edit_message(data)
        if endpoint == "deleteMessage":
            return self.__delete_message(data)
        if endpoint == "copyMessage":
            return self.__copy_message(data)
        if endpoint == "answerCallbackQuery":
            return True
        if endpoint == "getChat":
            return self.__chats.get(
                data["chat_id"],
                ChatFullInfo(
                    id=data["chat_id"],
                    username=f"@{data['chat_id']}",
                    first_name=str(data["chat_id"]),
                    type=Chat.PRIVATE,
                    accent_color_id=1,
                    max_reaction_count=1,
                    accepted_gift_types=AcceptedGiftTypes(False, False, False, False),
                ),
            ).to_dict()
        if endpoint == "forwardMessage":
            return self.__forward_message(data)
        if endpoint == "banChatMember":
            return self.__ban_chat_member(data)
        raise NotImplementedError(f"Endpoint {endpoint} not implemented")

    def __send_message(self, data: "MessageData") -> dict:
        reply_message = None
        if "reply_parameters" in data and data["reply_parameters"] is not None:
            reply_message = self.__simulator.get_message_by_id(data["reply_parameters"].message_id)
        message = Message(
            message_id=data.get("message_id", self.get_next_id()),
            date=datetime.now().timestamp(),
            chat=self.__chats.get(data["chat_id"], Chat(id=data["chat_id"], type=Chat.PRIVATE)),
            from_user=self.bot_user,
            text=data["text"],
            entities=data["entities"],
            reply_markup=data.get("reply_markup", None),
            reply_to_message=reply_message,
        )
        self.__simulator.add_message(message)
        return message.to_dict()

    def __forward_message(self, data: "MessageData") -> dict:
        forward_message = self.__simulator.get_message_by_id(data["message_id"])
        message = Message(
            message_id=self.get_next_id(),
            date=datetime.now().timestamp(),
            chat=self.__chats.get(data["chat_id"], Chat(id=data["chat_id"], type=Chat.PRIVATE)),
            from_user=self.bot_user,
            text=forward_message.text,
            entities=forward_message.entities,
            reply_markup=data.get("reply_markup", None),
            reply_to_message=forward_message.reply_to_message,
            forward_origin=self.get_forward_origin(forward_message),
        )
        self.__simulator.add_message(message)
        return message.to_dict()

    def __edit_message(self, data: "MessageData") -> dict:
        message = self.__simulator.get_message_by_id(data["message_id"])
        edited_dict = message.to_dict()
        if "text" in data:
            edited_dict["text"] = data["text"]
        if "entities" in data:
            edited_dict["entities"] = data["entities"]
        if "reply_markup" in data:
            edited_dict["reply_markup"] = None if data["reply_markup"] is None else data["reply_markup"].to_dict()
        self.__simulator.edit_message(Message.de_json(edited_dict, self.__bot))
        return edited_dict

    def __copy_message(self, data: "MessageData") -> dict:
        message = self.__simulator.get_message_by_id(data["message_id"])
        message_dict = message.to_dict()
        message_dict["message_id"] = self.get_next_id()
        message_dict["chat"] = self.__chats.get(data["chat_id"], Chat(id=data["chat_id"], type=Chat.PRIVATE)).to_dict()
        message_dict["from"] = self.bot_user.to_dict()
        if "reply_markup" in data:
            message_dict["reply_markup"] = None if data["reply_markup"] is None else data["reply_markup"].to_dict()
        if "reply_to_message_id" in data and data["reply_to_message_id"] is not None:
            message_dict["reply_to_message_id"] = self.__simulator.get_message_by_id(
                data["reply_to_message_id"]
            ).to_dict()
        self.__simulator.add_message(Message.de_json(message_dict, self.__bot))
        return message_dict

    def __delete_message(self, data: "MessageData") -> bool:
        self.__simulator.delete_message(data["message_id"])
        return True

    def __ban_chat_member(self, data: "MessageData") -> bool:
        """Bans a user from the chat by adding them to the banned users list

        Args:
            data: data containing user_id to ban

        Returns:
            True if the ban was successful
        """
        user_id = data["user_id"]
        user = SpottedUser(user_id)
        user.ban()
        return True

    def __get_me(self) -> dict:
        return {
            "id": self.bot_id,
            "is_bot": True,
            "first_name": self.bot_name,
            "username": self.bot_name,
            "can_join_groups": True,
            "can_read_all_group_messages": True,
            "supports_inline_queries": False,
        }

    @property
    def bot_user(self) -> User:
        return User(
            id=self.bot_id,
            is_bot=True,
            first_name=self.bot_name,
            username=self.bot_name,
        )

    @property
    def bot_name(self) -> str:
        return Config.settings_get("bot_tag").replace("@", "")

    @property
    def bot_id(self) -> int:
        return 1234567890
