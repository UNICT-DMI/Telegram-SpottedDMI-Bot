"""Pending post management"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import ClassVar, TypeAlias

from telegram import Message

from .db_manager import DbManager

_StoreKey: TypeAlias = tuple[int, int]


@dataclass()
class PendingPost:
    """Class that represents a pending post.
    The user_id is stored separately from the post data to strengthen anonymity:
    inspecting _store alone does not reveal who authored which post.

    Args:
        u_message_id: id of the original message of the post
        g_message_id: id of the post in the group
        admin_group_id: id of the admin group
        credit_username: username of the user that sent the post if it's a credit post
        date: when the post was sent
    """

    _store: ClassVar[dict[_StoreKey, "PendingPost"]] = {}
    _key_to_user: ClassVar[dict[_StoreKey, int]] = {}
    _user_to_key: ClassVar[dict[int, _StoreKey]] = {}
    _draining: ClassVar[bool] = False

    u_message_id: int
    g_message_id: int
    admin_group_id: int
    date: datetime
    credit_username: str | None = None

    @property
    def _key(self) -> _StoreKey:
        """Returns the store key for this post"""
        return (self.admin_group_id, self.g_message_id)

    @property
    def user_id(self) -> int:
        """Retrieves the user_id from the separate mapping"""
        return PendingPost._key_to_user[self._key]

    @classmethod
    def is_draining(cls) -> bool:
        """Returns whether the bot is in drain mode (shutting down)"""
        return cls._draining

    @classmethod
    def start_drain(cls):
        """Sets the drain flag, blocking new spot submissions"""
        cls._draining = True

    @classmethod
    def create(
        cls, user_message: Message, g_message_id: int, admin_group_id: int, credit_username: str | None = None
    ) -> "PendingPost":
        """Creates a new post and inserts it in the table of pending posts

        Args:
            user_message: message sent by the user that contains the post
            g_message_id: id of the post in the group
            admin_group_id: id of the admin group
            credit_username: username of the user that sent the post if it's a credit post

        Returns:
            instance of the class
        """
        user_id = user_message.from_user.id
        u_message_id = user_message.message_id
        date = datetime.now(tz=timezone.utc)

        return cls(
            u_message_id=u_message_id,
            g_message_id=g_message_id,
            admin_group_id=admin_group_id,
            credit_username=credit_username,
            date=date,
        ).save_post(user_id=user_id)

    @classmethod
    def from_group(cls, g_message_id: int, admin_group_id: int) -> "PendingPost | None":
        """Retrieves a pending post from the info related to the admin group

        Args:
            g_message_id: id of the post in the group
            admin_group_id: id of the admin group

        Returns:
            instance of the class
        """
        return cls._store.get((admin_group_id, g_message_id))

    @classmethod
    def from_user(cls, user_id: int) -> "PendingPost | None":
        """Retrieves a pending post from the user_id

        Args:
            user_id: id of the author of the post

        Returns:
            instance of the class
        """
        key = cls._user_to_key.get(user_id)
        if key is None:
            return None
        return cls._store.get(key)

    @staticmethod
    def get_all(admin_group_id: int, before: datetime | None = None) -> list["PendingPost"]:
        """Gets the list of pending posts in the specified admin group.
        If before is specified, returns only the one sent before that timestamp

        Args:
            admin_group_id: id of the admin group
            before: timestamp before which messages will be considered

        Returns:
            list of ids of pending posts
        """
        posts = []
        for post in PendingPost._store.values():
            if post.admin_group_id != admin_group_id:
                continue
            if before and post.date is not None:
                post_date = post.date.replace(tzinfo=None) if post.date.tzinfo else post.date
                before_date = before.replace(tzinfo=None) if before.tzinfo else before
                if post_date >= before_date:
                    continue
            posts.append(post)
        return posts

    def save_post(self, user_id: int) -> "PendingPost":
        """Saves the pending_post in the in-memory store and records the user mapping separately"""
        key = self._key
        PendingPost._store[key] = self
        PendingPost._key_to_user[key] = user_id
        PendingPost._user_to_key[user_id] = key
        return self

    def get_votes(self, vote: bool) -> int:
        """Gets all the votes of a specific kind (approve or reject)

        Args:
            vote: whether you look for the approve or reject votes

        Returns:
            number of votes
        """
        return DbManager.count_from(
            table_name="admin_votes",
            where="g_message_id = %s and admin_group_id = %s and is_upvote = %s",
            where_args=(self.g_message_id, self.admin_group_id, vote),
        )

    def get_credit_username(self) -> str | None:
        """Gets the username of the user that credited the post

        Returns:
            username of the user that credited the post, or None if the post is not credited
        """
        return self.credit_username

    def get_list_admin_votes(self, vote: "bool | None" = None) -> "list[int] | list[tuple[int, bool]]":
        """Gets the list of admins that approved or rejected the post

        Args:
            vote: whether you look for the approve or reject votes, or None if you want all the votes

        Returns:
            list of admins that approved or rejected a pending post
        """

        where = "g_message_id = %s and admin_group_id = %s"
        where_args = (self.g_message_id, self.admin_group_id)

        if vote is not None:
            where += " and is_upvote = %s"
            where_args = (self.g_message_id, self.admin_group_id, vote)

        votes = DbManager.select_from(
            select="admin_id, is_upvote", table_name="admin_votes", where=where, where_args=where_args
        )

        if vote is None:
            return [(v["admin_id"], v["is_upvote"]) for v in votes]

        return [v["admin_id"] for v in votes]

    def __get_admin_vote(self, admin_id: int) -> bool | None:
        """Gets the vote of a specific admin on a pending post

        Args:
            admin_id: id of the admin that voted

        Returns:
            a bool representing the vote or None if a vote was not yet made
        """
        vote = DbManager.select_from(
            select="is_upvote",
            table_name="admin_votes",
            where="admin_id = %s and g_message_id = %s and admin_group_id = %s",
            where_args=(admin_id, self.g_message_id, self.admin_group_id),
        )

        if len(vote) == 0:  # the vote is not present
            return None

        return vote[0]["is_upvote"]

    def set_admin_vote(self, admin_id: int, approval: bool) -> int:
        """Adds the vote of the admin on a specific post, or update the existing vote, if needed

        Args:
            admin_id: id of the admin that voted
            approval: whether the vote is approval or reject

        Returns:
            number of similar votes (all the approve or the reject), or -1 if the vote wasn't updated
        """
        vote = self.__get_admin_vote(admin_id)
        if vote is None:  # there isn't a vote yet
            DbManager.insert_into(
                table_name="admin_votes",
                columns=("admin_id", "g_message_id", "admin_group_id", "is_upvote", "credit_username", "message_date"),
                values=(admin_id, self.g_message_id, self.admin_group_id, approval, self.credit_username, self.date),
            )
            number_of_votes = self.get_votes(vote=approval)
        elif bool(vote) != approval:  # the vote was different from the approval
            DbManager.update_from(
                table_name="admin_votes",
                set_clause="is_upvote = %s",
                where="admin_id = %s and g_message_id = %s and admin_group_id = %s",
                args=(approval, admin_id, self.g_message_id, self.admin_group_id),
            )
            number_of_votes = self.get_votes(vote=approval)
        else:
            return -1
        return number_of_votes

    def delete_post(self):
        """Removes the post from the in-memory store, cleans up user mappings, and deletes votes from the database"""
        key = self._key
        user_id = PendingPost._key_to_user.pop(key, None)
        if user_id is not None:
            PendingPost._user_to_key.pop(user_id, None)
        PendingPost._store.pop(key, None)
        DbManager.delete_from(
            table_name="admin_votes",
            where="g_message_id = %s and admin_group_id = %s",
            where_args=(self.g_message_id, self.admin_group_id),
        )

    def __repr__(self) -> str:
        return (
            f"PendingPost: [ admin_group_id: {self.admin_group_id}\n"
            f"g_message_id: {self.g_message_id}\n"
            f"date : {self.date} ]"
        )
