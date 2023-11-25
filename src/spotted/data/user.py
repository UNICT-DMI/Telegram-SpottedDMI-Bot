"""Users management"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from random import choice

from telegram import Bot

from .config import Config
from .data_reader import read_md
from .db_manager import DbManager
from .pending_post import PendingPost


@dataclass()
class User:
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
    follow_date: datetime | None = None

    @property
    def is_pending(self) -> bool:
        """If the user has a post already pending or not"""
        return bool(PendingPost.from_user(self.user_id))

    @property
    def is_banned(self) -> bool:
        """If the user is banned or not"""
        return DbManager.count_from(table_name="banned_users", where="user_id = %s", where_args=(self.user_id,)) > 0

    @property
    def is_credited(self) -> bool:
        """If the user is in the credited list"""
        return DbManager.count_from(table_name="credited_users", where="user_id = %s", where_args=(self.user_id,)) == 1

    def get_n_warns(self) -> int:
        """_summary_

        Returns:
            int: _description_
        """
        return DbManager.count_from(table_name="warned_users", where="user_id = %s", where_args=self.user_id)

    @classmethod
    def banned_users(cls) -> "list[User]":
        """Returns a list of all the banned users"""
        return [
            cls(user_id=row["user_id"], ban_date=row["ban_date"])
            for row in DbManager.select_from(table_name="banned_users", select="user_id, ban_date")
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

    def ban_from_community(self, bot: Bot):
        bot.ban_chat_member(Config.post_get("community_group_id"), self.user_id)

    def mute(self, bot: Bot, days: int = 0):
        bot.restrict_chat_member(
            chat_id=Config.post_get("channel_id"),
            user_id=self.user_id,
            can_send_messages=False,
            can_send_media_messages=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False,
        )
        current_date_time = datetime.now()
        expiration_date_time = (current_date_time + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
        DbManager.insert_into(
            table_name="muted_users",
            columns=("user_id", "expiration_date"),
            values=(self.user_id, expiration_date_time),
        )

    def warn(self, bot: Bot):
        """_summary_"""
        n_warns = self.get_n_warns()

        if n_warns < 2:
            text = f"L'utente {self.user_id} è stato warnato."
            DbManager.insert_into(table_name="warned_users", columns="user_id", values=self.user_id)
        else:
            self.ban()
            self.ban_from_community(bot)
            text = f"L'utente {self.user_id} è stato bannato."
        bot.send_message(chat_id=Config.post_get("community_group_id"), text=text)

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
