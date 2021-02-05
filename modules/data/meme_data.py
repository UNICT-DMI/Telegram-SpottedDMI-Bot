"""Data management for the bot"""
from typing import Optional, Tuple
from datetime import datetime
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
        date = admin_message.date

        DbManager.insert_into(table_name="pending_meme",
                              columns=("user_id", "u_message_id", "g_message_id", "group_id", "message_date"),
                              values=(user_id, u_message_id, g_message_id, group_id, date))

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
    def get_list_admin_votes(g_message_id: int, group_id: int, vote: bool) -> Tuple[str]:
        """Gets the list of admins that approved or rejected a pending post

        Args:
            g_message_id (int): id of the post in question in the group
            group_id (int): id of the admin group
            vote (bool): whether you look for the approve or reject votes

        Returns:
            Tuple[str]: tuple of admins that approved or rejected a pending post
        """
        votes = DbManager.select_from(select="admin_id",
                                      table_name="admin_votes",
                                      where="g_message_id = %s and group_id = %s and is_upvote = %s",
                                      where_args=(g_message_id, group_id, vote))

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
    def get_list_pending_memes(group_id: int, before: datetime = None) -> Tuple[int]:
        """Gets the list of pending memes in the specified admin group.
        If before is specified, returns only the one sent before that timestamp

        Args:
            group_id (int): id of the admin group
            before (datetime, optional): timestamp before wich messages will be considered. Defaults to None.

        Returns:
            Tuple[str]: list of ids of pending memes
        """
        if datetime:
            list_pending_posts = DbManager.select_from(select="g_message_id",
                                                       table_name="pending_meme",
                                                       where="group_id = %s and (message_date < %s or message_date IS NULL)",
                                                       where_args=(group_id, before))
        else:
            list_pending_posts = DbManager.select_from(select="g_message_id",
                                                       table_name="pending_meme",
                                                       where="group_id = %s",
                                                       where_args=(group_id, ))
        return tuple([int(post['g_message_id']) for post in list_pending_posts])

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
    def cancel_pending_meme(user_id: int) -> tuple:
        """Removes a post that is still pending if the user so desires

        Args:
            user_id (int): id of the user that made the post

        Returns:
            tuple: if a pending post was deleted, returns its id and the admin group id, return None otherwise
        """
        result_row = DbManager.select_from(select='g_message_id, group_id',
                                           table_name='pending_meme',
                                           where='user_id = %s',
                                           where_args=(user_id, ))

        if len(result_row) == 0:  # there was no pending meme
            return None, None
        else:
            result_row = result_row[0]
            MemeData.remove_pending_meme(g_message_id=result_row['g_message_id'], group_id=result_row['group_id'])
            return result_row['g_message_id'], result_row['group_id']

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
    def set_user_report(user_id: int, target_username: str) -> None:
        """Adds the report of the user on a specific post

        Args:
            user_id (int): id of the user that reported
            target_username (str): username of reported user
        """
        DbManager.delete_from(table_name="user_report",
                              where="user_id = %s",
                              where_args=(user_id,))
        
        DbManager.insert_into(table_name="user_report",
                      columns=("user_id", "target_username", "message_date"),
                      values=(user_id, target_username, datetime.now()))

    @staticmethod
    def get_user_report(user_id: int, target_username: str = None) -> Optional[str]:
        """Gets the report of a specific user on a published post

        Args:
            user_id (int): id of the user that reported
            target_username (str): username of reported user

        Returns:
            Optional[str]: value of the report or None if a report was not yet made
        """

        if target_username:
            report = DbManager.select_from(select="*",
                                        table_name="user_report",
                                        where="user_id = %s and target_username = %s",
                                        where_args=(user_id, target_username))
        else:
            report = DbManager.select_from(select="*",
                                        table_name="user_report",
                                        where="user_id = %s",
                                        where_args=(user_id,))

        if len(report) == 0:  # the vote is not present
            return None
        return report[0]

    @staticmethod
    def set_post_report(user_id: int, c_message_id: int) -> bool:
        """Adds the report of the user on a specific post

        Args:
            user_id (int): id of the user that reported
            c_message_id (int): id of the post in question in the channel

        Returns:
            bool: whether the report was added or removed
        """
        current_report = MemeData.get_post_report(user_id, c_message_id)

        if current_report:  # there is a report
            return False
        
        DbManager.insert_into(table_name="spot_report",
                                columns=("user_id", "c_message_id"),
                                values=(user_id, c_message_id))            
        return True

    @staticmethod
    def get_post_report(user_id: int, c_message_id: int) -> Optional[str]:
        """Gets the report of a specific user on a published post

        Args:
            user_id (int): id of the user that reported
            c_message_id (int): id of the post in question in the channel

        Returns:
            Optional[str]: value of the report or None if a report was not yet made
        """

        report = DbManager.select_from(select="*",
                                     table_name="spot_report",
                                     where="user_id = %s and c_message_id = %s",
                                     where_args=(user_id, c_message_id))

        if len(report) == 0:  # the vote is not present
            return None
        return report[0]

    @staticmethod
    def get_last_post_report(user_id: int) -> Optional[str]:
        """Gets the last report of a specific user on a published post

        Args:
            user_id (int): id of the user that reported
            c_message_id (int): id of the post in question in the channel

        Returns:
            Optional[str]: last message id reported
        """

        report = DbManager.select_from(select="c_message_id",
                                     table_name="spot_report",
                                     where="user_id = %s",
                                     where_args=(user_id,),
                                     order_by="ROWID DESC")

        if len(report) == 0:  # the vote is not present
            return None
        return report[0]['c_message_id']

    @staticmethod
    def set_user_vote(user_id: int, c_message_id: int, channel_id: int, vote: str) -> bool:
        """Adds the vote of the user on a specific post, or update the existing vote, if needed

        Args:
            user_id (int): id of the user that voted
            c_message_id (int): id of the post in question in the channel
            channel_id (int): id of the channel
            vote (str): kind of vote the user wants to add or remove

        Returns:
            bool: whether the vote was added or removed
        """
        current_vote = MemeData.__get_user_vote(user_id, c_message_id, channel_id)
        vote_added = True
        if current_vote is None:  # there isn't a vote yet
            DbManager.insert_into(table_name="votes",
                                  columns=("user_id", "c_message_id", "channel_id", "vote"),
                                  values=(user_id, c_message_id, channel_id, vote))
        elif current_vote != vote:  # the old vote was different from the new vote
            DbManager.query_from_string(f"UPDATE votes SET vote = {vote}\
                                        WHERE user_id = '{user_id}'\
                                        and c_message_id = '{c_message_id}'\
                                        and channel_id = '{channel_id}'")
        else:  # the user wants to remove his vote
            DbManager.delete_from(table_name="votes",
                                  where="user_id = %s and c_message_id = %s and channel_id = %s",
                                  where_args=(user_id, c_message_id, channel_id))
            vote_added = False

        return vote_added

    @staticmethod
    def __get_user_vote(user_id: int, c_message_id: int, channel_id: int) -> Optional[str]:
        """Gets the vote of a specific user on a published post

        Args:
            user_id (int): id of the user that voted
            c_message_id (int): id of the post in question in the channel
            channel_id (int): id of the channel

        Returns:
            Optional[str]: value of the vote or None if a vote was not yet made
        """
        vote = DbManager.select_from(select="vote",
                                     table_name="votes",
                                     where="user_id = %s and c_message_id = %s and channel_id = %s",
                                     where_args=(user_id, c_message_id, channel_id))

        if len(vote) == 0:  # the vote is not present
            return None
        return vote[0]['vote']

    @staticmethod
    def get_published_votes(c_message_id: int, channel_id: int, vote: str) -> int:
        """Gets all the votes of a specific kind (upvote or downvote) on a published post

        Args:
            c_message_id (int): id of the post in question in the channel
            channel_id (int): id of the channel
            vote (str): kind of vote you are looking for

        Returns:
            int: number of votes
        """
        return DbManager.count_from(table_name="votes",
                                    where="c_message_id = %s and channel_id = %s and vote = %s",
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

    @staticmethod
    def get_n_posts() -> int:
        """Gets the total number of posts

        Returns:
            int: total number of posts
        """
        return DbManager.count_from(table_name="published_meme")

    @staticmethod
    def get_n_votes(vote: str = None) -> int:
        """Gets the total number of votes of the specified

        Args:
            vote (str, optional): type of votes to consider. None means all. Defaults to None.

        Returns:
            int: number of votes of the specified type
        """
        if vote is not None:
            return DbManager.count_from(table_name="votes", where="vote = %s", where_args=(vote, ))
        return DbManager.count_from(table_name="votes")

    @staticmethod
    def get_avg(vote: str = None) -> int:
        """Shows the average number of votes of the specified type per post

        Args:
            vote (str, optional): type of votes to consider. None means all. Defaults to None.

        Returns:
            int: average number of votes
        """
        avg = MemeData.get_n_votes(vote) / MemeData.get_n_posts()
        return round(avg, 2)

    @staticmethod
    def get_max_id(vote: str = None) -> Tuple[int, int, str]:
        """Gets the id of the post with the most votes of the specified type

        Args:
            vote (str, optional): type of votes to consider. None means all. Defaults to None.

        Returns:
            Tuple[int, int, int]: number of votes, id of the message, id of the channel
        """
        where = ""
        if vote is not None:
            where = f"WHERE v.vote = {vote}"

        sub_select = f"""(
                            SELECT COUNT(*) as n_votes, v.c_message_id as message_id, v.channel_id as channel_id
                            FROM votes as v 
                            {where}
                            GROUP BY v.c_message_id, v.channel_id
                            ORDER BY v.c_message_id DESC
                        )"""
        max_message = DbManager.select_from(select="MAX(n_votes) as max, message_id, channel_id", table_name=sub_select)
        return int(max_message[0]['max']), int(max_message[0]['message_id']), str(max_message[0]['channel_id'])
