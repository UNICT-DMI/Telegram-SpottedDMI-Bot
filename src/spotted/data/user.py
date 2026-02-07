"""Users management"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from random import choice

from telegram import Bot, ChatPermissions

from .config import Config
from .data_reader import read_md
from .db_manager import DbManager
from .pending_post import PendingPost


@dataclass()
class User:  # pylint: disable=too-many-public-methods
    """Class that represents a user

    Args:
        user_id: id of the user
        private_message_id: id of the private message sent by the user to the bot. Only used for following
        ban_date: datetime of when the user was banned. Only used for banned users
        follow_date: datetime of when the user started following a post. Only used for following users
    """

    user_id: int
    private_message_id: int | None = None
    ban_date: datetime | None = None
    mute_date: datetime | None = None
    mute_expire_date: datetime | None = None
    follow_date: datetime | None = None

    @property
    def is_pending(self) -> bool:
        """If the user has a post already pending or not"""
        return bool(PendingPost.from_user(self.user_id))

    @property
    def is_warn_bannable(self) -> bool:
        """If the user is bannable due to warns"""
        return self.get_n_warns() >= Config.post_get("max_n_warns")

    @property
    def is_banned(self) -> bool:
        """If the user is banned or not"""
        return DbManager.count_from(table_name="banned_users", where="user_id = %s", where_args=(self.user_id,)) > 0

    @property
    def is_muted(self) -> bool:
        """If the user is muted or not"""
        return DbManager.count_from(table_name="muted_users", where="user_id = %s", where_args=(self.user_id,)) > 0

    @property
    def is_credited(self) -> bool:
        """If the user is in the credited list"""
        return DbManager.count_from(table_name="credited_users", where="user_id = %s", where_args=(self.user_id,)) == 1

    @classmethod
    def banned_users(cls) -> "list[User]":
        """Returns a list of all the banned users"""
        return [
            cls(user_id=row["user_id"], ban_date=row["ban_date"])
            for row in DbManager.select_from(
                table_name="banned_users", select="user_id, ban_date", order_by="ban_date DESC"
            )
        ]

    @classmethod
    def muted_users(cls) -> "list[User]":
        """Returns a list of all the muted users"""
        return [
            cls(user_id=row["user_id"], mute_date=row["mute_date"], mute_expire_date=row["expire_date"])
            for row in DbManager.select_from(
                table_name="muted_users", select="user_id, mute_date, expire_date", order_by="mute_date DESC"
            )
        ]

    @classmethod
    def credited_users(cls) -> "list[User]":
        """Returns a list of all the credited users"""
        return [
            cls(user_id=row["user_id"]) for row in DbManager.select_from(table_name="credited_users", select="user_id")
        ]

    @classmethod
    def following_users(cls, message_id: int) -> "list[User]":
        """Returns a list of all the users following the post with the associated private message id
        used by the bot to send updates about the post by replying to it

        Args:
            message_id: id of the post the users are following

        Returns:
            list of users with private_message_id set to the id of the private message
            in the user's conversation with the bot
        """
        return [
            cls(user_id=row["user_id"], private_message_id=row["private_message_id"], follow_date=row["follow_date"])
            for row in DbManager.select_from(
                table_name="user_follow",
                select="user_id, private_message_id, follow_date",
                where="message_id = %s",
                where_args=(message_id,),
            )
        ]

    def get_n_warns(self) -> int:
        """Returns the count of consecutive warns of the user"""
        count = DbManager.count_from(table_name="warned_users", where="user_id = %s", where_args=(self.user_id,))
        return count if count else 0

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
            DbManager.delete_from(table_name="warned_users", where="user_id = %s", where_args=(self.user_id,))
            return True
        return False

    async def mute(self, bot: Bot | None, days: int):
        """Mute a user restricting its actions inside the community group

        Args:
            bot: the telegram bot
            days(optional): The number of days the user should be muted for.
        """
        if bot is not None:
            await bot.restrict_chat_member(
                chat_id=Config.post_get("community_group_id"),
                user_id=self.user_id,
                permissions=ChatPermissions(
                    can_send_messages=False,
                    can_send_other_messages=False,
                    can_add_web_page_previews=False,
                ),
            )
        expiration_date = datetime.now() + timedelta(days=days)
        DbManager.insert_into(
            table_name="muted_users",
            columns=("user_id", "expire_date"),
            values=(self.user_id, expiration_date),
        )

    async def unmute(self, bot: Bot | None) -> bool:
        """Unmute a user taking back all restrictions

        Args:
            bot : the telegram bot

        Returns:
            whether the user was muted before the unmute or not
        """
        # Just in case the user was manually muted by an admin,
        # we try to unmute him anyway, even if he is not in the muted list of the bot
        if bot is not None:
            await bot.restrict_chat_member(
                chat_id=Config.post_get("community_group_id"),
                user_id=self.user_id,
                permissions=ChatPermissions(
                    can_send_messages=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True,
                ),
            )

        if not self.is_muted:
            return False

        DbManager.delete_from(table_name="muted_users", where="user_id = %s", where_args=(self.user_id,))
        return True

    def warn(self):
        """Increase the number of warns of a user
        If the number of warns is greater than the maximum allowed, the user is banned

        Args:
            bot: the telegram bot
        """
        valid_until_date = datetime.now() + timedelta(days=Config.post_get("warn_expiration_days"))
        DbManager.insert_into(
            table_name="warned_users", columns=("user_id", "expire_date"), values=(self.user_id, valid_until_date)
        )

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

    async def get_user_sign(self, bot: Bot) -> str:
        """Generates a sign for the user. It will be a random name for an anonym user

        Args:
            bot: telegram bot

        Returns:
            the sign of the user
        """
        if self.is_credited:  # the user wants to be credited
            chat = await bot.get_chat(self.user_id)
            if chat.username:
                return f"@{chat.username}"

        return choice(read_md("anonym_names").split("\n"))  # random sign

    def is_following(self, message_id: int) -> bool:
        """Verifies if the user is following a post

        Args:
            message_id: id of the post

        Returns:
            whether the user is following the post or not
        """
        n_rows = DbManager.count_from(
            table_name="user_follow",
            where="user_id = %s and message_id = %s",
            where_args=(self.user_id, message_id),
        )
        return n_rows > 0

    def get_follow_private_message_id(self, message_id: int) -> int | None:
        """Verifies if the user is following a post

        Args:
            message_id: id of the post

        Returns:
            whether the user is following the post or not
        """
        result = DbManager.select_from(
            table_name="user_follow",
            select="private_message_id",
            where="user_id = %s and message_id = %s",
            where_args=(self.user_id, message_id),
        )
        return result[0]["private_message_id"] if result else None

    def set_follow(self, message_id: int, private_message_id: int | None):
        """Sets the follow status of the user.
        If the private_message_id is None, the user is not following the post anymore,
        and the record is deleted from the database.
        Otherwise, the user is following the post and a new record is created.

        Args:
            message_id: id of the post
            private_message_id: id of the private message. If None, the record is deleted
        """
        if private_message_id is None:
            DbManager.delete_from(
                table_name="user_follow",
                where="user_id = %s and message_id = %s",
                where_args=(self.user_id, message_id),
            )
        DbManager.insert_into(
            table_name="user_follow",
            columns=("user_id", "message_id", "private_message_id"),
            values=(self.user_id, message_id, private_message_id),
        )

    def __repr__(self) -> str:
        return (
            f"User: [ user_id: {self.user_id}\n"
            f"is_pending: {self.is_pending}\n"
            f"is_credited: {self.is_credited}\n"
            f"is_banned: {self.is_banned} ]"
        )
