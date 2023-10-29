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
            table_name="published_meme",
            where="channel_id = %s and c_message_id = %s",
            where_args=(channel_id, c_message_id),
        )
        if not is_present:
            return None

        return cls(channel_id=channel_id, c_message_id=c_message_id)

    def save_post(self) -> "PublishedPost":
        """Saves the published_post in the database"""
        DbManager.insert_into(
            table_name="published_meme",
            columns=("channel_id", "c_message_id"),
            values=(self.channel_id, self.c_message_id),
        )
        return self

    def __get_user_vote(self, user_id: int) -> Optional[str]:
        """Gets the vote of a specific user on the post

        Args:
            user_id: id of the user that voted

        Returns:
            value of the vote or None if a vote was not yet made
        """
        vote = DbManager.select_from(
            select="vote",
            table_name="votes",
            where="user_id = %s and c_message_id = %s and channel_id = %s",
            where_args=(user_id, self.c_message_id, self.channel_id),
        )

        if len(vote) == 0:  # the vote is not present
            return None
        return vote[0]["vote"]

    def set_user_vote(self, user_id: int, vote: str) -> bool:
        """Adds the vote of the user on the post, updates the existing vote or deletes it

        Args:
            user_id: id of the user that voted
            vote: kind of vote the user wants to add or remove

        Returns:
            whether the vote was added or removed
        """
        current_vote = self.__get_user_vote(user_id=user_id)
        if current_vote is None:  # there isn't a vote yet
            DbManager.insert_into(
                table_name="votes",
                columns=("user_id", "c_message_id", "channel_id", "vote"),
                values=(user_id, self.c_message_id, self.channel_id, vote),
            )
        elif current_vote != vote:  # the old vote was different from the new vote
            DbManager.update_from(
                table_name="votes",
                set_clause="vote = %s",
                where="user_id = %s and c_message_id = %s and channel_id = %s",
                args=(vote, user_id, self.c_message_id, self.channel_id),
            )
        else:  # the user wants to remove his vote
            DbManager.delete_from(
                table_name="votes",
                where="user_id = %s and c_message_id = %s and channel_id = %s",
                where_args=(user_id, self.c_message_id, self.channel_id),
            )
            return False

        return True

    def get_votes(self, vote: str) -> int:
        """Gets all the votes of a specific kind on the post

        Args:
            vote: kind of vote you are looking for

        Returns:
            number of votes
        """
        return DbManager.count_from(
            table_name="votes",
            where="c_message_id = %s and channel_id = %s and vote = %s",
            where_args=(self.c_message_id, self.channel_id, vote),
        )

    def set_votes(self, keyboard: InlineKeyboardMarkup):
        """Sets all the votes of the post based on the inline keyboard.
        This means that all previous votes associated with this post, if present, will be replaced

        Args:
            keyboard: posts inline keyboard
        """
        DbManager.delete_from(
            table_name="votes",
            where="c_message_id = %s and channel_id = %s",
            where_args=(self.c_message_id, self.channel_id),
        )
        ids = -1
        for row in keyboard.inline_keyboard:
            for column in row:
                data = str(column.callback_data)
                if data.startswith("meme_vote,"):
                    n_votes = int(column.text.split(" ")[1])
                    vote = data.split(",")[1]
                    for _ in range(n_votes):
                        self.set_user_vote(user_id=ids, vote=vote)
                        ids -= 1

    def __repr__(self) -> str:
        return f"PublishedPost: [ channel_id: {self.channel_id}\n" f"c_message_id: {self.c_message_id} ]"
