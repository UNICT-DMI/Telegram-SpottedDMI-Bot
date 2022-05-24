"""Reports management"""
from dataclasses import dataclass
from datetime import datetime
from telegram import Message
from .db_manager import DbManager


@dataclass(slots=True)
class Report():
    """Class that represents a report

    Args:
        user_id: id of the user that reported
        group_id: id of the admin group
        g_message_id: id of the post in the group
        channel_id: id of the channel
        c_message_id: id of the post in question in the channel
        target_username: username of the reported user
        date: when the report happened
    """
    user_id: int
    group_id: int
    g_message_id: int
    channel_id: int = None
    c_message_id: int = None
    target_username: str = None
    date: datetime = None

    @property
    def minutes_passed(self) -> float:
        """:class:`float`:Ammount of minutes elapsed from when the report was submitted, if applicable"""
        if self.date is None:
            return -1

        delta_time = datetime.now() - self.date
        return delta_time.total_seconds() / 60

    @classmethod
    def create_post_report(cls, user_id: int, channel_id: int, c_message_id: int, admin_message: Message):
        """Adds the report of the user on a specific post

        Args:
            user_id: id of the user that reported
            channel_id: id of the channel
            c_message_id: id of the post in question in the channel
            admin_message: message received in the admin group that references the report

        Returns:
            istance of the class or None if the report was not created
        """

        g_message_id = admin_message.message_id
        group_id = admin_message.chat_id

        current_report = cls.get_post_report(user_id, channel_id, c_message_id)

        if current_report:  # there is already a report, the creation fails
            return None

        return cls(user_id=user_id,
                   channel_id=channel_id,
                   c_message_id=c_message_id,
                   group_id=group_id,
                   g_message_id=g_message_id).save_report()

    @classmethod
    def create_user_report(cls, user_id: int, target_username: str, admin_message: Message):
        """Adds the report of the user targetting another user

        Args:
            user_id: id of the user that reported
            target_username: username of reported user
            admin_message: message received in the admin group that references the report

        Returns:
            istance of the class
        """

        g_message_id = admin_message.message_id
        group_id = admin_message.chat_id
        date = datetime.now()

        return cls(user_id=user_id, group_id=group_id, g_message_id=g_message_id, target_username=target_username, date=date) \
                .save_report()

    @classmethod
    def get_post_report(cls, user_id: int, channel_id: int, c_message_id: int):
        """Gets the report of a specific user on a published post

        Args:
            user_id: id of the user that reported
            channel_id: id of the channel
            c_message_id: id of the post in question in the channel

        Returns:
            istance of the class or None if the report was not present
        """

        reports = DbManager.select_from(select="*",
                                        table_name="spot_report",
                                        where="user_id = %s and channel_id = %s and c_message_id = %s",
                                        where_args=(user_id, channel_id, c_message_id))
        if len(reports) == 0:  # the report is not present
            return None

        report = reports[0]
        return cls(user_id=report['user_id'],
                   channel_id=report['channel_id'],
                   c_message_id=report['c_message_id'],
                   group_id=report['group_id'],
                   g_message_id=report['g_message_id'])

    @classmethod
    def get_last_user_report(cls, user_id: int):
        """Gets the last user report of a specific user

        Args:
            user_id: id of the user that reported

        Returns:
            istance of the class or None if the report was not present
        """
        reports = DbManager.select_from(select="*",
                                        table_name="user_report",
                                        where="user_id = %s",
                                        where_args=(user_id,),
                                        order_by="message_date DESC")

        if len(reports) == 0:  # the vote is not present
            return None
        report = reports[0]
        return cls(user_id=report['user_id'],
                   target_username=report['target_username'],
                   date=datetime.strptime(report['message_date'], "%Y-%m-%d %H:%M:%S.%f"),
                   group_id=report['group_id'],
                   g_message_id=report['g_message_id'])

    @classmethod
    def from_group(cls, group_id: int, g_message_id: int):
        """Gets a report of any type related to the specified message in the admin group

        Args:
            group_id: id of the admin group
            g_message_id: id of the report in the group

        Returns:
            istance of the class or None if the report was not present
        """
        reports = DbManager.select_from(select="*",
                                        table_name="user_report",
                                        where="group_id = %s and g_message_id = %s",
                                        where_args=(group_id, g_message_id))

        if len(reports) > 0:  # the vote is not present
            report = reports[0]
            return cls(user_id=report['user_id'],
                       target_username=report['target_username'],
                       date=datetime.strptime(report['message_date'], "%Y-%m-%d %H:%M:%S.%f"),
                       group_id=report['group_id'],
                       g_message_id=report['g_message_id'])

        reports = DbManager.select_from(select="*",
                                        table_name="spot_report",
                                        where="group_id = %s and g_message_id = %s",
                                        where_args=(group_id, g_message_id))

        if len(reports) > 0:  # the vote is not present
            report = reports[0]
            return cls(user_id=report['user_id'],
                       c_message_id=report['c_message_id'],
                       group_id=report['group_id'],
                       g_message_id=report['g_message_id'])

        return None

    def save_report(self):
        """Saves the report in the database"""
        if self.c_message_id is not None:
            DbManager.insert_into(table_name="spot_report",
                                  columns=("user_id", "channel_id", "c_message_id", "group_id", "g_message_id"),
                                  values=(self.user_id, self.channel_id, self.c_message_id, self.group_id, self.g_message_id))
        else:
            DbManager.insert_into(table_name="user_report",
                                  columns=("user_id", "target_username", "message_date", "group_id", "g_message_id"),
                                  values=(self.user_id, self.target_username, self.date, self.group_id, self.g_message_id))
        return self

    def __repr__(self):
        if self.c_message_id is not None:
            return f"PostReport: [ user_id: {self.user_id}\n"\
                    f"channel_id: {self.channel_id}\n"\
                    f"c_message_id: {self.c_message_id}\n"\
                    f"group_id: {self.group_id}\n"\
                    f"g_message_id: {self.g_message_id} ]"
        return f"UserReport: [ user_id: {self.user_id}\n"\
                f"target_username: {self.target_username}\n"\
                f"date: {self.date}\n"\
                f"group_id: {self.group_id}\n"\
                f"g_message_id: {self.g_message_id} ]"
