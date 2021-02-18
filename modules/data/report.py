"""Reports management"""
from datetime import datetime
from telegram import Message
from modules.data.db_manager import DbManager


class Report():
    """Class that represents a report
    """
    def __init__(self,
                 user_id: int,
                 group_id: int,
                 g_message_id: int,
                 c_message_id: int = None,
                 target_username: str = None,
                 date: datetime = None):
        self.user_id = user_id
        self.group_id = group_id
        self.g_message_id = g_message_id
        self.c_message_id = c_message_id
        self.target_username = target_username
        self.date = date

    @property
    def minutes_passed(self) -> float:
        """Calculates the ammount of minutes elapsed from when the report was submitted, if applicable

        Returns:
            float: how many minutes have enlapsed, if applicable, -1 otherwise
        """
        if self.date is None:
            return -1

        delta_time = datetime.now() - self.date
        return delta_time.total_seconds() / 60

    @classmethod
    def create_post_report(cls, user_id: int, c_message_id: int, admin_message: Message):
        """Adds the report of the user on a specific post

        Args:
            user_id (int): id of the user that reported
            c_message_id (int): id of the post in question in the channel
            admin_message (Message): message received in the admin group that references the report

        Returns:
            Report: istance of the class or None if the report was not created
        """

        g_message_id = admin_message.message_id
        group_id = admin_message.chat_id

        current_report = Report.get_post_report(user_id, c_message_id)

        if current_report:  # there is already a report, the creation fails
            return None

        DbManager.insert_into(table_name="spot_report",
                              columns=("user_id", "c_message_id", "group_id", "g_message_id"),
                              values=(user_id, c_message_id, group_id, g_message_id))
        return cls(user_id=user_id, c_message_id=c_message_id, group_id=group_id, g_message_id=g_message_id)

    @classmethod
    def create_user_report(cls, user_id: int, target_username: str, admin_message: Message):
        """Adds the report of the user targetting another user

        Args:
            user_id (int): id of the user that reported
            target_username (str): username of reported user
            admin_message (Message): message received in the admin group that references the report

        Returns:
            Report: istance of the class
        """

        g_message_id = admin_message.message_id
        group_id = admin_message.chat_id
        date = datetime.now()

        DbManager.insert_into(table_name="user_report",
                              columns=("user_id", "target_username", "message_date", "group_id", "g_message_id"),
                              values=(user_id, target_username, date, group_id, g_message_id))

        return cls(user_id=user_id,
                   group_id=group_id,
                   g_message_id=g_message_id,
                   target_username=target_username,
                   date=date)

    @classmethod
    def get_post_report(cls, user_id: int, c_message_id: int):
        """Gets the report of a specific user on a published post

        Args:
            user_id (int): id of the user that reported
            c_message_id (int): id of the post in question in the channel

        Returns:
            Report: istance of the class or None if the report was not present
        """

        reports = DbManager.select_from(select="*",
                                        table_name="spot_report",
                                        where="user_id = %s and c_message_id = %s",
                                        where_args=(user_id, c_message_id))
        if len(reports) == 0:  # the report is not present
            return None

        report = reports[0]
        return cls(user_id=report['user_id'],
                   c_message_id=report['c_message_id'],
                   group_id=report['group_id'],
                   g_message_id=report['g_message_id'])

    @classmethod
    def get_last_user_report(cls, user_id: int):
        """Gets the last user report of a specific user

        Args:
            user_id (int): id of the user that reported

        Returns:
            Report: istance of the class or None if the report was not present
        """
        reports = DbManager.select_from(select="*",
                                        table_name="user_report",
                                        where="user_id = %s",
                                        where_args=(user_id, ),
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
            group_id (int): id of the admin group
            g_message_id (int): id of the report in the group

        Returns:
            Report: istance of the class or None if the report was not present
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

    def __repr__(self):
        if self.c_message_id is not None:
            return f"PostReport: [ user_id: {self.user_id}\n"\
                    f"c_message_id: {self.c_message_id}\n"\
                    f"group_id: {self.group_id}\n"\
                    f"g_message_id: {self.g_message_id} ]"
        else:
            return f"UserReport: [ user_id: {self.user_id}\n"\
                    f"target_username: {self.target_username}\n"\
                    f"date: {self.date}\n"\
                    f"group_id: {self.group_id}\n"\
                    f"g_message_id: {self.g_message_id} ]"
