"""Users management"""
from modules.data.db_manager import DbManager
from modules.data.pending_post import PendingPost


class User():
    """Class that represents a user
    """
    def __init__(self, user_id):
        self.user_id = user_id

    @property
    def is_pending(self) -> bool:
        """Checks if the user has a post already pending or not

        Returns:
            bool: whether the user has a post already pending or not
        """
        return bool(PendingPost.from_user(self.user_id))

    @property
    def is_banned(self) -> bool:
        """Checks if the user is banned or not

        Returns:
            bool: whether the user is banned or not
        """
        return DbManager.count_from(table_name="banned_users", where="user_id = %s", where_args=(self.user_id, )) > 0

    @property
    def is_credited(self) -> bool:
        """Checks if the user is in the credited list

        Returns:
            bool: whether the user is to be credited or not
        """
        return DbManager.count_from(table_name="credited_users", where="user_id = %s", where_args=(self.user_id, )) == 1

    def ban(self):
        """Adds the user to the banned list
        """
        if not self.is_banned:
            DbManager.insert_into(table_name="banned_users", columns=("user_id", ), values=(self.user_id, ))

    def sban(self) -> bool:
        """Removes the user from the banned list

        Returns:
            bool: whether the user was present in the banned list before the sban or not
        """
        if self.is_banned:
            DbManager.delete_from(table_name="banned_users", where="user_id = %s", where_args=(self.user_id, ))
            return True
        return False

    def become_anonym(self) -> bool:
        """Removes the user from the credited list, if he was present

        Returns:
            bool: whether the user was already anonym
        """
        already_anonym = not self.is_credited
        if not already_anonym:
            DbManager.delete_from(table_name="credited_users", where="user_id = %s", where_args=(self.user_id, ))
        return already_anonym

    def become_credited(self) -> bool:
        """Adds the user to the credited list, if he wasn't already credited

        Returns:
            bool: whether the user was already credited
        """
        already_credited = self.is_credited
        if not already_credited:
            DbManager.insert_into(table_name="credited_users", columns=("user_id", ), values=(self.user_id, ))
        return already_credited

    def __repr__(self):
        return f"User: [ user_id: {self.user_id}\n"\
                f"is_pending: {self.is_pending}\n"\
                f"is_credited: {self.is_credited}\n"\
                f"is_banned: {self.is_banned} ]"
