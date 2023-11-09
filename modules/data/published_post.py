"""Published post management"""
from dataclasses import dataclass
from typing import Optional
from telegram import InlineKeyboardMarkup
from .db_manager import DbManager


@dataclass()
class PublishedPost:
    """Class that represents a published post

    Args:
        channel_id: id of the channel
        c_message_id: id of the post in the channel
    """

    channel_id: int
    c_message_id: int

    @classmethod
    def create(cls, channel_id: int, c_message_id: int) -> "PublishedPost":
        """Inserts a new post in the table of published posts

        Args:
            channel_id: id of the channel
            c_message_id: id of the post in the channel

        Returns:
            instance of the class
        """
        return cls(channel_id=channel_id, c_message_id=c_message_id).save_post()

    @classmethod
    def from_channel(cls, channel_id: int, c_message_id: int) -> Optional["PublishedPost"]:
        """Retrieves a published post from the info related to the channel

        Args:
            channel_id: id of the channel
            c_message_id: id of the post in the channel

        Returns:
            instance of the class
        """
        is_present = DbManager.count_from(
            table_name="published_post",
            where="channel_id = %s and c_message_id = %s",
            where_args=(channel_id, c_message_id),
        )
        if not is_present:
            return None

        return cls(channel_id=channel_id, c_message_id=c_message_id)

    def save_post(self) -> "PublishedPost":
        """Saves the published_post in the database"""
        DbManager.insert_into(
            table_name="published_post",
            columns=("channel_id", "c_message_id"),
            values=(self.channel_id, self.c_message_id),
        )
        return self

    def __repr__(self) -> str:
        return f"PublishedPost: [ channel_id: {self.channel_id}\n" f"c_message_id: {self.c_message_id} ]"
