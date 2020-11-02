"""Data management for the meme bot"""
from typing import Optional, Tuple
from telegram import Message
from modules.data.db_manager import DbManager
from modules.data.data_reader import config_map

if config_map['meme']['reset_on_load']:
    DbManager.query_from_file("data", "db", "meme_db_del.sql")
DbManager.query_from_file("data", "db", "meme_db_init.sql")


# region db management
class MemeData():
    """Class that handles the management of persistent data fetch or manipulation in the meme bot
    """
    @staticmethod
    def insert_pending_post(user_message: Message, admin_message: Message):
        """Insert a new post in the table of pending posts

        Args:
            user_message (Message): message sent by the user that contains the post
            admin_message (Message): message recieved in the admin group that references the post
        """
        user_id = user_message.from_user.id
        u_message_id = user_message.message_id
        g_message_id = admin_message.message_id
        group_id = admin_message.chat_id

        DbManager.insert_into(table_name="pending_meme",
                              columns=("user_id", "u_message_id", "g_message_id", "group_id"),
                              values=(user_id, u_message_id, g_message_id, group_id))

    @staticmethod
    def set_admin_vote(admin_id: int, g_message_id: int, group_id: int, approval: bool) -> int:
        """Adds the vote of the admin on a specific post, or update the existing vote, if needed

        Args:
            admin_id (int): id of the admin that voted
            g_message_id (int): id of the post in question in the group
            group_id (int): id of the admin group
            approval (bool): whether the vote is approval or reject

        Returns:
            int: number of similar votes (all the approve or the reject), or -1 if the vote wasn't updated
        """
        vote = MemeData.__get_admin_vote(admin_id, g_message_id, group_id)
        if vote is None:  # there isn't a vote yet
            DbManager.insert_into(table_name="admin_votes",
                                  columns=("admin_id", "g_message_id", "group_id", "is_upvote"),
                                  values=(admin_id, g_message_id, group_id, approval))
            number_of_votes = MemeData.get_pending_votes(g_message_id, group_id, approval)
        elif bool(vote) != approval:  # the vote was different from the approval
            DbManager.query_from_string(f"UPDATE admin_votes SET is_upvote = {approval}\
                                    WHERE admin_id = '{admin_id}'\
                                        and g_message_id = '{g_message_id}'\
                                        and group_id = '{group_id}'")
            number_of_votes = MemeData.get_pending_votes(g_message_id, group_id, approval)
        else:
            return -1
        return number_of_votes

    @staticmethod
    def __get_admin_vote(admin_id: int, g_message_id: int, group_id: int) -> Optional[bool]:
        """Gets the vote of a specific admin on a pending post

        Args:
            admin_id (int): id of the admin that voted
            g_message_id (int): id of the post in question in the group
            group_id (int): id of the admin group

        Returns:
            Optional[bool]: a bool representing the vote or None if a vote was not yet made
        """
        vote = DbManager.select_from(select="is_upvote",
                                     table_name="admin_votes",
                                     where="admin_id = %s and g_message_id = %s and group_id = %s",
                                     where_args=(admin_id, g_message_id, group_id))

        if len(vote) == 0:  # the vote is not present
            return None

        return vote[0]['is_upvote']

    @staticmethod
    def get_admin_list_votes(g_message_id: int, group_id: int, approve: bool) -> Tuple[str]:
        """Gets the vote of a specific admin on a pending post

        Args:
            admin_id (int): id of the admin that voted
            g_message_id (int): id of the post in question in the group
            group_id (int): id of the admin group

        Returns:
            Optional[bool]: a bool representing the vote or None if a vote was not yet made
        """
        votes = DbManager.select_from(select="admin_id",
                                     table_name="admin_votes",
                                     where="g_message_id = %s and group_id = %s and is_upvote = %s",
                                     where_args=(g_message_id, group_id, approve))

        if len(votes) == 0:  # the vote is not present
            return None

        return tuple([vote['admin_id'] for vote in votes])

    @staticmethod
    def get_pending_votes(g_message_id: int, group_id: int, vote: bool) -> int:
        """Gets all the votes of a specific kind (approve or reject) on a pending post

        Args:
            g_message_id (int): id of the post in question in the group
            group_id (int): id of the admin group
            vote (bool): whether you look for the approve or reject votes

        Returns:
            int: number of votes
        """
        return DbManager.count_from(table_name="admin_votes",
                                    where="g_message_id = %s and group_id = %s and is_upvote = %s",
                                    where_args=(g_message_id, group_id, vote))

    @staticmethod
    def remove_pending_meme(g_message_id: int, group_id: int):
        """Removes all entries on a post that is no longer pending

        Args:
            g_message_id (int): id of the no longer pending post in the group
            group_id (int): id of the admin group
        """
        DbManager.delete_from(table_name="pending_meme",
                              where="g_message_id = %s and group_id = %s",
                              where_args=(g_message_id, group_id))
        DbManager.delete_from(table_name="admin_votes",
                              where="g_message_id = %s and group_id = %s",
                              where_args=(g_message_id, group_id))

    @staticmethod
    def insert_published_post(channel_message: Message):
        """Inserts a new post in the table of pending posts

        Args:
            channel_message (Message): message approved to be published
        """
        c_message_id = channel_message.message_id
        channel_id = channel_message.chat_id
        DbManager.insert_into(table_name="published_meme",
                              columns=("channel_id", "c_message_id"),
                              values=(channel_id, c_message_id))

    @staticmethod
    def set_user_vote(user_id: int, c_message_id: int, channel_id: int, vote: bool) -> Tuple[int, bool]:
        """Adds the vote of the user on a specific post, or update the existing vote, if needed

        Args:
            user_id (int): id of the user that voted
            c_message_id (int): id of the post in question in the channel
            channel_id (int): id of the channel
            vote (bool): whether it is an upvote or a downvote

        Returns:
            Tuple[int, bool]: number of similar votes (all the upvotes or the downvotes), or -1 if the vote wasn't updated, \
                whether or not the vote was added or removed
        """
        current_vote = MemeData.__get_user_vote(user_id, c_message_id, channel_id)
        vote_added = True
        if current_vote is None:  # there isn't a vote yet
            DbManager.insert_into(table_name="votes",
                                  columns=("user_id", "c_message_id", "channel_id", "is_upvote"),
                                  values=(user_id, c_message_id, channel_id, vote))
        elif bool(current_vote) != vote:  # the old vote was different from the new vote
            DbManager.query_from_string(f"UPDATE votes SET is_upvote = {vote}\
                                        WHERE user_id = '{user_id}'\
                                        and c_message_id = '{c_message_id}'\
                                        and channel_id = '{channel_id}'")
        else:  # the user wants to remove his vote
            DbManager.delete_from(table_name="votes",
                                  where="user_id = %s and c_message_id = %s and channel_id = %s",
                                  where_args=(user_id, c_message_id, channel_id))
            vote_added = False

        number_of_votes = MemeData.get_published_votes(c_message_id, channel_id, vote)
        return number_of_votes, vote_added

    @staticmethod
    def __get_user_vote(user_id: int, c_message_id: int, channel_id: int) -> Optional[bool]:
        """Gets the vote of a specific user on a published post

        Args:
            user_id (int): id of the user that voted
            c_message_id (int): id of the post in question in the channel
            channel_id (int): id of the channel

        Returns:
            Optional[bool]: a bool representing the vote or None if a vote was not yet made
        """
        vote = DbManager.select_from(select="is_upvote",
                                     table_name="votes",
                                     where="user_id = %s and c_message_id = %s and channel_id = %s",
                                     where_args=(user_id, c_message_id, channel_id))

        if len(vote) == 0:  # the vote is not present
            return None
        return vote[0]['is_upvote']

    @staticmethod
    def get_published_votes(c_message_id: int, channel_id: int, vote: bool) -> int:
        """Gets all the votes of a specific kind (upvote or downvote) on a published post

        Args:
            c_message_id (int): id of the post in question in the channel
            channel_id (int): id of the channel
            vote (bool): whether you look for upvotes or downvotes

        Returns:
            int: number of votes
        """
        return DbManager.count_from(table_name="votes",
                                    where="c_message_id = %s and channel_id = %s and is_upvote = %s",
                                    where_args=(c_message_id, channel_id, vote))

    @staticmethod
    def get_user_id(g_message_id: int, group_id: int) -> Optional[int]:
        """Gets the user_id of the user that made the pending post

        Args:
            g_message_id (int): id of the post in question in the group
            group_id (int): id of the admin group

        Returns:
            Optional[int]: user_id, if found
        """
        list_user_id = DbManager.select_from(select="user_id",
                                             table_name="pending_meme",
                                             where="g_message_id = %s and group_id = %s",
                                             where_args=(g_message_id, group_id))
        if list_user_id:
            return list_user_id[0]['user_id']
        return None

    @staticmethod
    def is_banned(user_id: int) -> bool:
        """Checks if the user is banned or not

        Args:
            user_id (int): id of the user to check

        Returns:
            bool: whether the user is banned or not
        """
        return DbManager.count_from(table_name="banned_users", where="user_id = %s", where_args=(user_id, )) > 0

    @staticmethod
    def is_pending(user_id: int) -> bool:
        """Checks if the user still has a post pending

        Args:
            user_id (int): id of the user to check

        Returns:
            bool: whether the user still has a post pending or not
        """
        return DbManager.count_from(table_name="pending_meme", where="user_id = %s", where_args=(user_id, )) > 0

    @staticmethod
    def ban_user(user_id: int):
        """Adds the user to the banned list

        Args:
            user_id (int): id of the user to ban
        """
        DbManager.insert_into(table_name="banned_users", columns=("user_id", ), values=(user_id, ))

    @staticmethod
    def sban_user(user_id: int) -> bool:
        """Removes the user from the banned list

        Args:
            user_id (int): id of the user to sban

        Returns:
            bool: whether the user was present in the banned list before the sban or not
        """
        out = DbManager.count_from(table_name="banned_users", where="user_id = %s", where_args=(user_id, ))
        if out > 0:
            DbManager.delete_from(table_name="banned_users", where="user_id = %s", where_args=(user_id, ))
        return out

    @staticmethod
    def become_anonym(user_id: int) -> bool:
        """Removes the user from the credited list, if he was present

        Args:
            user_id (int): id of the user to make anonym

        Returns:
            bool: whether the user was already anonym
        """
        already_anonym = not MemeData.is_credited(user_id)
        if not already_anonym:
            DbManager.delete_from(table_name="credited_users", where="user_id = %s", where_args=(user_id, ))
        return already_anonym

    @staticmethod
    def become_credited(user_id: int) -> bool:
        """Adds the user to the credited list, if he wasn't already credited

        Args:
            user_id (int): id of the user to credit

        Returns:
            bool: whether the user was already credited
        """
        already_credited = MemeData.is_credited(user_id)
        if not already_credited:
            DbManager.insert_into(table_name="credited_users", columns=("user_id", ), values=(user_id, ))
        return already_credited

    @staticmethod
    def is_credited(user_id: int) -> bool:
        """Checks if the user is in the credited list

        Args:
            user_id (int): id of the user to check

        Returns:
            bool: whether the user is to be credited or not
        """
        return DbManager.count_from(table_name="credited_users", where="user_id = %s", where_args=(user_id, )) == 1
