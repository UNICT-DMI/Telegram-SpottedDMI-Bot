"""Users management"""
from random import choice
from attr import dataclass
from telegram import Bot
from .data_reader import read_md
from .db_manager import DbManager
from .pending_post import PendingPost


@dataclass()
class User():
    """Class that represents a user

    Args:
        user_id: id of the user
    """
    user_id: int

    @property
    def is_pending(self) -> bool:
        """:class:`bool`: If the user has a post already pending or not"""
        return bool(PendingPost.from_user(self.user_id))

    @property
    def is_banned(self) -> bool:
        """:class:`bool`: If the user is banned or not"""
        return DbManager.count_from(table_name="banned_users", where="user_id = %s", where_args=(self.user_id,)) > 0

    @property
    def is_credited(self) -> bool:
        """:class:`bool`: If the user is in the credited list"""
        return DbManager.count_from(table_name="credited_users", where="user_id = %s", where_args=(self.user_id,)) == 1

    def ban(self):
        """Adds the user to the banned list"""

        if not self.is_banned:
            DbManager.insert_into(table_name="banned_users", columns=("user_id",), values=(self.user_id,))

    def sban(self) -> bool:
        """Removes the user from the banned list

        Returns:
            whether the user was present in the banned list before the sban or not
        """
        if self.is_banned:
            DbManager.delete_from(table_name="banned_users", where="user_id = %s", where_args=(self.user_id,))
            return True
        return False

    def become_anonym(self) -> bool:
        """Removes the user from the credited list, if he was present

        Returns:
            whether the user was already anonym
        """
        already_anonym = not self.is_credited
        if not already_anonym:
            DbManager.delete_from(table_name="credited_users", where="user_id = %s", where_args=(self.user_id,))
        return already_anonym

    def become_credited(self) -> bool:
        """Adds the user to the credited list, if he wasn't already credited

        Returns:
            whether the user was already credited
        """
        already_credited = self.is_credited
        if not already_credited:
            DbManager.insert_into(table_name="credited_users", columns=("user_id",), values=(self.user_id,))
        return already_credited

    def get_user_sign(self, bot: Bot) -> str:
        """Generates a sign for the user. It will be a random name for an anonym user

        Args:
            bot: telegram bot

        Returns:
            the sign of the user
        """
        sign = choice(read_md("anonym_names").split("\n"))  # random sign
        if self.is_credited:  # the user wants to be credited
            username = bot.get_chat(self.user_id).username
            if username:
                sign = "@" + username

        return sign

    def __repr__(self):
        return f"User: [ user_id: {self.user_id}\n"\
                f"is_pending: {self.is_pending}\n"\
                f"is_credited: {self.is_credited}\n"\
                f"is_banned: {self.is_banned} ]"
