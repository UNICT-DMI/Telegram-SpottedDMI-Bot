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
