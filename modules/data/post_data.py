"""Data management for the bot"""
from .db_manager import DbManager


class PostData:
    """Class that handles the management of persistent data fetch or manipulation in the post bot"""

    @staticmethod
    def get_n_posts() -> int:
        """Gets the total number of posts

        Returns:
            total number of posts
        """
        return DbManager.count_from(table_name="published_post")

    @staticmethod
    def get_n_votes(vote: str | None = None) -> int:
        """Gets the total number of votes of the specified

        Args:
            vote: type of votes to consider. None means all

        Returns:
            number of votes of the specified type
        """
        if vote is not None:
            return DbManager.count_from(table_name="votes", where="vote = %s", where_args=(vote,))
        return DbManager.count_from(table_name="votes")

    @staticmethod
    def get_avg(vote: str | None = None) -> int:
        """Shows the average number of votes of the specified type per post

        Args:
            vote: type of votes to consider. None means all

        Returns:
            average number of votes
        """
        tot_posts = PostData.get_n_posts()
        avg = PostData.get_n_votes(vote) / (tot_posts if tot_posts != 0 else 1)
        return round(avg, 2)

    @staticmethod
    def get_max_id(vote: str | None = None) -> tuple[int, int, str]:
        """Gets the id of the post with the most votes of the specified type

        Args:
            vote: type of votes to consider. None means all

        Returns:
            number of votes, id of the message, id of the channel
        """
        where = ""
        where_args = None
        if vote is not None:
            where = "WHERE v.vote = ?"  # ? placeholder
            where_args = (vote,)

        sub_select = f"""(
                            SELECT COUNT(*) as n_votes, v.c_message_id as message_id, v.channel_id as channel_id
                            FROM votes as v 
                            {where}
                            GROUP BY v.c_message_id, v.channel_id
                            ORDER BY v.c_message_id DESC
                        )"""
        max_message = DbManager.select_from(
            select="MAX(n_votes) as max, message_id, channel_id", table_name=sub_select, where_args=where_args
        )

        if len(max_message) == 0 or max_message[0]["max"] is None:  # there is no post with the requested vote
            return 0, 0, "0"
        return int(max_message[0]["max"]), int(max_message[0]["message_id"]), str(max_message[0]["channel_id"])
