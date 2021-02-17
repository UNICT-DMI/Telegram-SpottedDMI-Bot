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
    def set_user_report(user_id: int, target_username: str, admin_message: Message) -> None:
        """Adds the report of the user on a specific post

        Args:
            user_id (int): id of the user that reported
            target_username (str): username of reported user
            admin_message (Message): message received in the admin group that references the report
        """

        g_message_id = admin_message.message_id
        group_id = admin_message.chat_id

        DbManager.insert_into(table_name="user_report",
                            columns=("user_id", "target_username", "message_date", "group_id", "g_message_id"),
                            values=(user_id, target_username, datetime.now(), group_id, g_message_id))

    @staticmethod
    def get_user_report(user_id: int) -> Optional[str]:
        """Gets the report of a specific user on a published post

        Args:
            user_id (int): id of the user that reported

        Returns:
            Optional[str]: value of the report or None if a report was not yet made
        """

        report = DbManager.select_from(select="*",
                                    table_name="user_report",
                                    where="user_id = %s",
                                    where_args=(user_id,),
                                    order_by="ROWID DESC")

        if len(report) == 0:  # the vote is not present
            return None
        return report[0]

    @staticmethod
    def set_post_report(user_id: int, c_message_id: int, admin_message: Message) -> bool:
        """Adds the report of the user on a specific post

        Args:
            user_id (int): id of the user that reported
            c_message_id (int): id of the post in question in the channel
            admin_message (Message): message received in the admin group that references the report

        Returns:
            bool: whether the report was added or removed
        """

        g_message_id = admin_message.message_id
        group_id = admin_message.chat_id

        current_report = MemeData.get_post_report(user_id, c_message_id)

        if current_report:  # there is a report
            return False

        DbManager.insert_into(table_name="spot_report",
                                columns=("user_id", "c_message_id", "group_id", "g_message_id"),
                                values=(user_id, c_message_id, group_id, g_message_id))
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
    def get_user_id(g_message_id: int, group_id: int) -> Optional[int]:
        """Gets the user_id of the user that made the report

        Args:
            g_message_id (int): id of the post in question in the group
            group_id (int): id of the admin group

        Returns:
            Optional[int]: user_id, if found
        """
        list_user_id = DbManager.select_from(select="user_id",
                                            table_name="spot_report",
                                            where="g_message_id = %s and group_id = %s",
                                            where_args=(g_message_id, group_id))

        if list_user_id:
            return list_user_id[0]['user_id']

        list_user_id = DbManager.select_from(select="user_id",
                                            table_name="user_report",
                                            where="g_message_id = %s and group_id = %s",
                                            where_args=(g_message_id, group_id))

        if list_user_id:
            return list_user_id[0]['user_id']

        return None


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
