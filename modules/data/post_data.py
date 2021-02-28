"""Data management for the bot"""
from typing import Tuple
from modules.data.db_manager import DbManager


class PostData():
    """Class that handles the management of persistent data fetch or manipulation in the meme bot
    """
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
        avg = PostData.get_n_votes(vote) / PostData.get_n_posts()
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

        if max_message[0]['max'] is None:  # there is no post with the requested vote
            return 0, 0, "0"
        return int(max_message[0]['max']), int(max_message[0]['message_id']), str(max_message[0]['channel_id'])
