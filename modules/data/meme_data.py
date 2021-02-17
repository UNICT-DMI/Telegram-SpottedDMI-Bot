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
