"""Reports management"""
from dataclasses import dataclass
from datetime import datetime

from telegram import Message

from .db_manager import DbManager


@dataclass()
class Report:
    """Class that represents a report

    Args:
        user_id: id of the user that reported
        admin_group_id: id of the admin group
        g_message_id: id of the post in the group
        channel_id: id of the channel
        c_message_id: id of the post in question in the channel
        target_username: username of the reported user
        date: when the report happened
    """

    user_id: int
    admin_group_id: int
    g_message_id: int
    channel_id: int = None
    c_message_id: int = None
    target_username: str = None
    date: datetime = None

    @property
    def minutes_passed(self) -> float:
        """:class:`float`:Amount of minutes elapsed from when the report was submitted, if applicable"""
        if self.date is None:
            return -1

        delta_time = datetime.now() - self.date
        return delta_time.total_seconds() / 60

    @classmethod
    def create_post_report(
        cls, user_id: int, channel_id: int, c_message_id: int, admin_message: Message
    ) -> "Report | None":
        """Adds the report of the user on a specific post

        Args:
            user_id: id of the user that reported
            channel_id: id of the channel
            c_message_id: id of the post in question in the channel
            admin_message: message received in the admin group that references the report

        Returns:
            instance of the class or None if the report was not created
        """

        g_message_id = admin_message.message_id
        admin_group_id = admin_message.chat_id

        current_report = cls.get_post_report(user_id, channel_id, c_message_id)

        if current_report:  # there is already a report, the creation fails
            return None

        return cls(
            user_id=user_id,
            channel_id=channel_id,
            c_message_id=c_message_id,
            admin_group_id=admin_group_id,
            g_message_id=g_message_id,
            date=datetime.now(),
        ).save_report()

    @classmethod
    def create_user_report(cls, user_id: int, target_username: str, admin_message: Message) -> "Report":
        """Adds the report of the user targeting another user

        Args:
            user_id: id of the user that reported
            target_username: username of reported user
            admin_message: message received in the admin group that references the report

        Returns:
            instance of the class
        """

        g_message_id = admin_message.message_id
        admin_group_id = admin_message.chat_id

        return cls(
            user_id=user_id,
            admin_group_id=admin_group_id,
            g_message_id=g_message_id,
            target_username=target_username,
            date=datetime.now(),
        ).save_report()

    @classmethod
    def get_post_report(cls, user_id: int, channel_id: int, c_message_id: int) -> "Report | None":
        """Gets the report of a specific user on a published post

        Args:
            user_id: id of the user that reported
            channel_id: id of the channel
            c_message_id: id of the post in question in the channel

        Returns:
            instance of the class or None if the report was not present
        """

        reports = DbManager.select_from(
            select="*",
            table_name="spot_report",
            where="user_id = %s and channel_id = %s and c_message_id = %s",
            where_args=(user_id, channel_id, c_message_id),
        )
        if len(reports) == 0:  # the report is not present
            return None

        report = reports[0]
        return cls(
            user_id=report["user_id"],
            channel_id=report["channel_id"],
            c_message_id=report["c_message_id"],
            admin_group_id=report["admin_group_id"],
            g_message_id=report["g_message_id"],
            date=report["message_date"],
        )

    @classmethod
    def get_last_user_report(cls, user_id: int) -> "Report | None":
        """Gets the last user report of a specific user

        Args:
            user_id: id of the user that reported

        Returns:
            instance of the class or None if the report was not present
        """
        reports = DbManager.select_from(
            select="*",
            table_name="user_report",
            where="user_id = %s",
            where_args=(user_id,),
            order_by="message_date DESC",
        )

        if len(reports) == 0:  # the vote is not present
            return None
        report = reports[0]
        return cls(
            user_id=report["user_id"],
            target_username=report["target_username"],
            date=report["message_date"],
            admin_group_id=report["admin_group_id"],
            g_message_id=report["g_message_id"],
        )

    @classmethod
    def from_group(cls, admin_group_id: int, g_message_id: int) -> "Report | None":
        """Gets a report of any type related to the specified message in the admin group

        Args:
            admin_group_id: id of the admin group
            g_message_id: id of the report in the group

        Returns:
            instance of the class or None if the report was not present
        """
        reports = DbManager.select_from(
            select="*",
            table_name="user_report",
            where="admin_group_id = %s and g_message_id = %s",
            where_args=(admin_group_id, g_message_id),
        )

        if len(reports) > 0:  # the report has been found
            report = reports[0]
            return cls(
                user_id=report["user_id"],
                target_username=report["target_username"],
                date=report["message_date"],
                admin_group_id=report["admin_group_id"],
                g_message_id=report["g_message_id"],
            )

        reports = DbManager.select_from(
            select="*",
            table_name="spot_report",
            where="admin_group_id = %s and g_message_id = %s",
            where_args=(admin_group_id, g_message_id),
        )

        if len(reports) > 0:  # the report has been found
            report = reports[0]
            return cls(
                user_id=report["user_id"],
                c_message_id=report["c_message_id"],
                admin_group_id=report["admin_group_id"],
                g_message_id=report["g_message_id"],
                date=report["message_date"],
            )

        return None

    def save_report(self) -> "Report":
        """Saves the report in the database"""
        if self.c_message_id is not None:
            DbManager.insert_into(
                table_name="spot_report",
                columns=("user_id", "channel_id", "message_date", "c_message_id", "admin_group_id", "g_message_id"),
                values=(
                    self.user_id,
                    self.channel_id,
                    self.date,
                    self.c_message_id,
                    self.admin_group_id,
                    self.g_message_id,
                ),
            )
        else:
            DbManager.insert_into(
                table_name="user_report",
                columns=("user_id", "target_username", "message_date", "admin_group_id", "g_message_id"),
                values=(self.user_id, self.target_username, self.date, self.admin_group_id, self.g_message_id),
            )
        return self

    def __repr__(self) -> str:
        if self.c_message_id is not None:
            return (
                f"PostReport: [ user_id: {self.user_id}\n"
                f"channel_id: {self.channel_id}\n"
                f"c_message_id: {self.c_message_id}\n"
                f"date: {self.date}\n"
                f"admin_group_id: {self.admin_group_id}\n"
                f"g_message_id: {self.g_message_id} ]"
            )
        return (
            f"UserReport: [ user_id: {self.user_id}\n"
            f"target_username: {self.target_username}\n"
            f"date: {self.date}\n"
            f"admin_group_id: {self.admin_group_id}\n"
            f"g_message_id: {self.g_message_id} ]"
        )
