"""Pending post management"""
from typing import Optional, Tuple
from datetime import datetime, timezone
from telegram import Message, Bot
from modules.data.db_manager import DbManager
from modules.data.data_reader import config_map


class PendingPost():
    """Class that represents a pending post

    Args:
        user_id (:class:`int`): id of the user that sent the post
        u_message_id (:class:`int`): id of the original message of the post
        group_id (:class:`int`): id of the admin group
        g_message_id (:class:`int`): id of the post in the group
        date (:class:`datetime`): when the post was sent
    """

    def __init__(self, user_id: int, u_message_id: int, g_message_id: int, group_id: int, date: datetime):
        self.user_id = user_id
        self.u_message_id = u_message_id
        self.group_id = group_id
        self.g_message_id = g_message_id
        self.date = date

    @classmethod
    def create(cls, user_message: Message, g_message_id: int, group_id: int):
        """Creates a new post and inserts it in the table of pending posts

        Args:
            user_message (Message): message sent by the user that contains the post
            g_message_id (int): id of the post in the group
            group_id (int): id of the admin group

        Returns:
            PendingPost: istance of the class
        """
        user_id = user_message.from_user.id
        u_message_id = user_message.message_id
        date = datetime.now(tz=timezone.utc)

        return cls(user_id=user_id, u_message_id=u_message_id, g_message_id=g_message_id, group_id=group_id, date=date) \
                .save_post()

    @classmethod
    def from_group(cls, g_message_id: int, group_id: int):
        """Retrieves a pending post from the info related to the admin group

        Args:
            g_message_id (int): id of the post in the group
            group_id (int): id of the admin group

        Returns:
            PendingPost: istance of the class
        """
        pending_post_arr = DbManager.select_from(select="*",
                                                 table_name="pending_meme",
                                                 where="group_id = %s and g_message_id = %s",
                                                 where_args=(group_id, g_message_id))
        if not pending_post_arr:
            return None

        pending_post = pending_post_arr[0]
        return cls(user_id=pending_post['user_id'],
                   u_message_id=pending_post['u_message_id'],
                   group_id=pending_post['group_id'],
                   g_message_id=pending_post['g_message_id'],
                   date=pending_post['message_date'])

    @classmethod
    def from_user(cls, user_id: int):
        """Retrieves a pending post from the user_id

        Args:
            user_id (int): id of the author of the post

        Returns:
            PendingPost: istance of the class
        """
        pending_post_arr = DbManager.select_from(select="*",
                                                 table_name="pending_meme",
                                                 where="user_id = %s",
                                                 where_args=(user_id,))
        if not pending_post_arr:
            return None

        pending_post = pending_post_arr[0]
        return cls(user_id=pending_post['user_id'],
                   u_message_id=pending_post['u_message_id'],
                   group_id=pending_post['group_id'],
                   g_message_id=pending_post['g_message_id'],
                   date=pending_post['message_date'])

    @staticmethod
    def get_all_pending_memes(group_id: int, before: datetime = None) -> list:
        """Gets the list of pending memes in the specified admin group.
        If before is specified, returns only the one sent before that timestamp

        Args:
            group_id (int): id of the admin group
            before (datetime, optional): timestamp before wich messages will be considered. Defaults to None.

        Returns:
            List[type(PendingPost)]: list of ids of pending memes
        """
        if datetime:
            pending_posts_id = DbManager.select_from(select="g_message_id",
                                                     table_name="pending_meme",
                                                     where="group_id = %s and (message_date < %s or message_date IS NULL)",
                                                     where_args=(group_id, before))
        else:
            pending_posts_id = DbManager.select_from(select="g_message_id",
                                                     table_name="pending_meme",
                                                     where="group_id = %s",
                                                     where_args=(group_id,))
        pending_posts = []
        for post in pending_posts_id:
            g_message_id = int(post['g_message_id'])
            pending_posts.append(PendingPost.from_group(group_id=group_id, g_message_id=g_message_id))
        return pending_posts

    def save_post(self):
        """Saves the pending_post in the database"""
        DbManager.insert_into(table_name="pending_meme",
                              columns=("user_id", "u_message_id", "g_message_id", "group_id", "message_date"),
                              values=(self.user_id, self.u_message_id, self.g_message_id, self.group_id, self.date))
        return self

    def get_votes(self, vote: bool):
        """Gets all the votes of a specific kind (approve or reject)

        Args:
            vote (bool): whether you look for the approve or reject votes

        Returns:
            int: number of votes
        """
        return DbManager.count_from(table_name="admin_votes",
                                    where="g_message_id = %s and group_id = %s and is_upvote = %s",
                                    where_args=(self.g_message_id, self.group_id, vote))

    def get_list_admin_votes(self, vote: bool) -> Tuple[str]:
        """Gets the list of admins that approved or rejected the post

        Args:
            vote (bool): whether you look for the approve or reject votes

        Returns:
            Tuple[str]: tuple of admins that approved or rejected a pending post
        """
        votes = DbManager.select_from(select="admin_id",
                                      table_name="admin_votes",
                                      where="g_message_id = %s and group_id = %s and is_upvote = %s",
                                      where_args=(self.g_message_id, self.group_id, vote))

        if len(votes) == 0:  # the vote is not present
            return None

        return tuple([vote['admin_id'] for vote in votes])

    def show_admins_votes(self, bot: Bot, approve: bool):
        """After a post is been approved or rejected, shows the admins that aproved or rejected it \
            and edit the message to delete the reply_markup

        Args:
            bot (Bot): bot
            approve (bool): whether the vote is approve or reject
        """
        admins = self.get_list_admin_votes(vote=approve)
        text = "Approvato da:\n" if approve else "Rifiutato da:\n"
        tag = '@' if config_map['meme']['tag'] else ''
        for admin in admins:
            username = bot.get_chat(admin).username
            text += f"{tag}{username}\n" if username else f"{bot.get_chat(admin).first_name}\n"

        bot.edit_message_reply_markup(chat_id=self.group_id, message_id=self.g_message_id, reply_markup=None)
        bot.send_message(chat_id=self.group_id, text=text, reply_to_message_id=self.g_message_id)

    def __get_admin_vote(self, admin_id: int) -> Optional[bool]:
        """Gets the vote of a specific admin on a pending post

        Args:
            admin_id (int): id of the admin that voted

        Returns:
            Optional[bool]: a bool representing the vote or None if a vote was not yet made
        """
        vote = DbManager.select_from(select="is_upvote",
                                     table_name="admin_votes",
                                     where="admin_id = %s and g_message_id = %s and group_id = %s",
                                     where_args=(admin_id, self.g_message_id, self.group_id))

        if len(vote) == 0:  # the vote is not present
            return None

        return vote[0]['is_upvote']

    def set_admin_vote(self, admin_id: int, approval: bool) -> int:
        """Adds the vote of the admin on a specific post, or update the existing vote, if needed

        Args:
            admin_id (int): id of the admin that voted
            approval (bool): whether the vote is approval or reject

        Returns:
            int: number of similar votes (all the approve or the reject), or -1 if the vote wasn't updated
        """
        vote = self.__get_admin_vote(admin_id)
        if vote is None:  # there isn't a vote yet
            DbManager.insert_into(table_name="admin_votes",
                                  columns=("admin_id", "g_message_id", "group_id", "is_upvote"),
                                  values=(admin_id, self.g_message_id, self.group_id, approval))
            number_of_votes = self.get_votes(vote=approval)
        elif bool(vote) != approval:  # the vote was different from the approval
            DbManager.update_from(table_name="admin_votes",
                                  set_clause="is_upvote = %s",
                                  where="admin_id = %s and g_message_id = %s and group_id = %s",
                                  args=(approval, admin_id, self.g_message_id, self.group_id))
            number_of_votes = self.get_votes(vote=approval)
        else:
            return -1
        return number_of_votes

    def delete_post(self):
        """Removes all entries on a post that is no longer pending
        """
        DbManager.delete_from(table_name="pending_meme",
                              where="g_message_id = %s and group_id = %s",
                              where_args=(self.g_message_id, self.group_id))
        DbManager.delete_from(table_name="admin_votes",
                              where="g_message_id = %s and group_id = %s",
                              where_args=(self.g_message_id, self.group_id))
        self.user_id = None
        self.u_message_id = None
        self.group_id = None
        self.g_message_id = None
        self.date = None

    def __repr__(self):
        return f"PendingPost: [ user_id: {self.user_id}\n"\
                f"u_message_id: {self.u_message_id}\n"\
                f"group_id: {self.group_id}\n"\
                f"g_message_id: {self.g_message_id}\n"\
                f"date : {self.date} ]"
