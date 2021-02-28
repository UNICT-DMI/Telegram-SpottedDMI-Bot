"""Published post management"""
from typing import Optional
from telegram import Message
from modules.data.db_manager import DbManager


class PublishedPost():
    """Class that represents a published post
    """
    def __init__(self, channel_id: int, c_message_id: int):
        self.channel_id = channel_id
        self.c_message_id = c_message_id

    @classmethod
    def create(cls, channel_message: Message):
        """Inserts a new post in the table of published posts

        Args:
            channel_message (Message): message ready to be published

        Returns:
            PublishedPost: istance of the class
        """
        c_message_id = channel_message.message_id
        channel_id = channel_message.chat_id
        DbManager.insert_into(table_name="published_meme",
                              columns=("channel_id", "c_message_id"),
                              values=(channel_id, c_message_id))
        return cls(channel_id=channel_id, c_message_id=c_message_id)

    @classmethod
    def from_channel(cls, channel_id: int, c_message_id: int):
        """Retrieves a published post from the info related to the channel

        Args:
            channel_id (int): id of the channel
            c_message_id (int): id of the post in the channel

        Returns:
            PublishedPost: istance of the class
        """
        is_present = DbManager.count_from(table_name="published_meme",
                                          where="channel_id = %s and c_message_id = %s",
                                          where_args=(channel_id, c_message_id))
        if not is_present:
            return None

        return cls(channel_id=channel_id, c_message_id=c_message_id)

    def __get_user_vote(self, user_id: int) -> Optional[str]:
        """Gets the vote of a specific user on the post

        Args:
            user_id (int): id of the user that voted

        Returns:
            Optional[str]: value of the vote or None if a vote was not yet made
        """
        vote = DbManager.select_from(select="vote",
                                     table_name="votes",
                                     where="user_id = %s and c_message_id = %s and channel_id = %s",
                                     where_args=(user_id, self.c_message_id, self.channel_id))

        if len(vote) == 0:  # the vote is not present
            return None
        return vote[0]['vote']

    def set_user_vote(self, user_id: int, vote: str) -> bool:
        """Adds the vote of the user on the post, updates the existing vote or deletes it

        Args:
            user_id (int): id of the user that voted
            vote (str): kind of vote the user wants to add or remove

        Returns:
            bool: whether the vote was added or removed
        """
        current_vote = self.__get_user_vote(user_id=user_id)
        if current_vote is None:  # there isn't a vote yet
            DbManager.insert_into(table_name="votes",
                                  columns=("user_id", "c_message_id", "channel_id", "vote"),
                                  values=(user_id, self.c_message_id, self.channel_id, vote))
        elif current_vote != vote:  # the old vote was different from the new vote
            DbManager.query_from_string(f"UPDATE votes SET vote = {vote}\
                                        WHERE user_id = '{user_id}'\
                                        and c_message_id = '{self.c_message_id}'\
                                        and channel_id = '{self.channel_id}'")
        else:  # the user wants to remove his vote
            DbManager.delete_from(table_name="votes",
                                  where="user_id = %s and c_message_id = %s and channel_id = %s",
                                  where_args=(user_id, self.c_message_id, self.channel_id))
            return False

        return True

    def get_votes(self, vote: str) -> int:
        """Gets all the votes of a specific kind on the post

        Args:
            vote (str): kind of vote you are looking for

        Returns:
            int: number of votes
        """
        return DbManager.count_from(table_name="votes",
                                    where="c_message_id = %s and channel_id = %s and vote = %s",
                                    where_args=(self.c_message_id, self.channel_id, vote))

    def __repr__(self):
        return f"PublishedPost: [ channel_id: {self.channel_id}\n"\
                f"c_message_id: {self.c_message_id} ]"
