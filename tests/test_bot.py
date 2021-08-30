# pylint: disable=unused-argument,redefined-outer-name
"""Tests the bot functionality"""
from datetime import datetime
from typing import Tuple
import pytest
from telegram import Chat, Message
from tests.util import TelegramSimulator
from modules.data import config_map, read_md, DbManager, User, PendingPost, PublishedPost, Report
from modules.handlers.constants import CHAT_PRIVATE_ERROR


@pytest.fixture(scope="function")
def local_table(init_local_test_db: DbManager) -> DbManager:
    """Called once per at the beginning of each function.
    Resets the state of the database
    """
    init_local_test_db.query_from_file("data", "db", "meme_db_del.sql")
    init_local_test_db.query_from_file("data", "db", "meme_db_init.sql")
    return init_local_test_db


@pytest.fixture(scope="function")
def telegram(local_table: DbManager) -> TelegramSimulator:
    """Called once per at the beginning of each function.
    Creates a telegram simulator object

    Returns:
        telegram weaver
    """
    return TelegramSimulator()


@pytest.fixture(scope="function")
def pending_post_message(local_table: DbManager, admin_group: Chat) -> Message:
    """Called once per at the beginning of each function.
    Simulates an existing pending post

    Returns:
        pending post message
    """
    PendingPost(1, 0, 0, config_map['meme']['group_id'], datetime.now()).save_post()
    return Message(message_id=0, date=datetime.now(), chat=admin_group)


@pytest.fixture(scope="function")
def published_post_message(telegram: TelegramSimulator, channel: Chat, channel_group: Chat) -> Message:
    """Called once per at the beginning of each function.
    Simulates an existing published post

    Returns:
        published post message
    """
    c_message = Message(message_id=0, date=datetime.now(), chat=channel)
    telegram.add_message(c_message)

    if config_map['meme']['comments']:
        f_message = Message(message_id=1,
                            date=datetime.now(),
                            chat=channel_group,
                            forward_from_message_id=0,
                            forward_from_chat=channel)
        g_message = Message(message_id=2, date=datetime.now(), chat=channel_group, reply_to_message=f_message)
        PublishedPost(channel_group.id, g_message.message_id).save_post()
        telegram.add_message(f_message)
        telegram.add_message(g_message)
        return g_message

    PublishedPost(channel.id, c_message.message_id).save_post()
    telegram.add_message(c_message)
    return c_message


@pytest.fixture(scope="function")
def report_user_message(local_table: DbManager, admin_group: Chat) -> Message:
    """Called once per at the beginning of each function.
    Simulates an existing user report

    Returns:
        user report message
    """
    Report(1, config_map['meme']['group_id'], 0, target_username='BadUser', date=datetime.now()).save_report()
    return Message(message_id=0, date=datetime.now(), chat=admin_group)


@pytest.fixture(scope="function")
def report_spot_message(local_table: DbManager, admin_group: Chat, channel: Chat) -> Tuple[Message, Message]:
    """Called once per at the beginning of each function.
    Simulates an existing spot report

    Returns:
        spot report in the admin group and post in the channel
    """
    Report(1,
           config_map['meme']['group_id'],
           0,
           channel_id=config_map['meme']['channel_id'],
           c_message_id=1,
           date=datetime.now()).save_report()
    group_message = Message(message_id=0, date=datetime.now(), chat=admin_group)
    channel_message = Message(message_id=1, date=datetime.now(), chat=channel)
    return group_message, channel_message


@pytest.fixture(scope="class")
def channel() -> Chat:
    """Called once per at the beginning of each function.
    Returns the channel chat

    Returns:
        admin user
    """
    group_id = config_map['meme']['channel_id']
    return Chat(id=group_id, type=Chat.CHANNEL)


@pytest.fixture(scope="class")
def admin_group() -> Chat:
    """Called once per at the beginning of each function.
    Returns the admin group chat

    Returns:
        admin user
    """
    group_id = config_map['meme']['group_id']
    return Chat(id=group_id, type=Chat.GROUP)


@pytest.fixture(scope="class")
def channel_group() -> Chat:
    """Called once per at the beginning of each function.
    Returns the chat of the public group with the comments

    Returns:
        admin user
    """
    channel_group_id = config_map['meme']['group_id']
    return Chat(id=channel_group_id, type=Chat.GROUP)


class TestBot:
    """Tests the bot simulating the telegram API's responses"""

    class TestBotBasicCommand:
        """Tests the bot commands"""

        def test_start_cmd(self, telegram: TelegramSimulator):
            """Tests the /start command.
            The bot sends the start response to the user
            """
            telegram.send_command("/start")
            assert telegram.last_message.text == read_md("start")

        def test_help_user_cmd(self, telegram: TelegramSimulator):
            """Tests the /help command.
            The bot sends the help response to the user
            """
            telegram.send_command("/help")
            assert telegram.last_message.text == read_md("help")

        def test_help_admin_cmd(self, telegram: TelegramSimulator, admin_group: Chat):
            """Tests the /help command.
            The bot sends the help response to the admins
            """
            telegram.send_command("/help", chat=admin_group)
            assert telegram.last_message.text == read_md("instructions")

        def test_rules_cmd(self, telegram: TelegramSimulator):
            """Tests the /rules command.
            The bot sends the rules response to the user
            """
            telegram.send_command("/rules")
            assert telegram.last_message.text == read_md("rules")

    class TestBotAdminCommand:
        """Tests the bot commands reserved for admins"""

        def test_ban_cmd(self, telegram: TelegramSimulator, admin_group: Chat, pending_post_message: Message):
            """Tests the /ban command.
            The bot bans the user associated with the pending post
            """
            telegram.send_message("/ban", chat=admin_group, reply_to_message=pending_post_message)
            assert telegram.last_message.text == "L'utente è stato bannato"
            assert PendingPost.from_group(pending_post_message.message_id, pending_post_message.chat_id) is None
            assert User(1).is_banned

        def test_sban_invalid_cmd(self, telegram: TelegramSimulator, admin_group: Chat):
            """Tests the /sban command.
            The bot warns about invalid command
            """
            telegram.send_command("/sban", chat=admin_group)
            assert telegram.last_message.text == "[uso]: /sban <user_id1> [...user_id2]"

        def test_sban_cmd(self, telegram: TelegramSimulator, admin_group: Chat):
            """Tests the /sban command.
            The bot sbans the users specified user
            """
            User(1).ban()
            telegram.send_command("/sban 1", chat=admin_group)
            assert telegram.last_message.text == "Sban effettuato"
            assert not User(1).is_banned

        def test_reply_invalid_cmd(self, telegram: TelegramSimulator, admin_group: Chat, pending_post_message: Message):
            """Tests the /reply command.
            The bot warns about invalid command
            """
            telegram.send_message("/reply", chat=admin_group, reply_to_message=pending_post_message)
            assert telegram.last_message.text.startswith("La reply è vuota\n")

        def test_reply_post_cmd(self, telegram: TelegramSimulator, admin_group: Chat, pending_post_message: Message):
            """Tests the /reply command.
            The bot sends a message to the user on behalf of the admin
            """
            telegram.send_message("/reply TEST", chat=admin_group, reply_to_message=pending_post_message)
            assert telegram.messages[-2].text.startswith("COMUNICAZIONE DEGLI ADMIN SUL TUO ULTIMO POST:\n")
            assert telegram.messages[-2].text.endswith("TEST")
            assert telegram.last_message.text.startswith("L'utente ha ricevuto il seguente messaggio:\n")
            assert telegram.last_message.text.endswith("TEST")

        def test_reply_report_user_cmd(self, telegram: TelegramSimulator, admin_group: Chat, report_user_message: Message):
            """Tests the /reply command.
            The bot sends a message to the user on behalf of the admin
            """
            telegram.send_message("/reply TEST", chat=admin_group, reply_to_message=report_user_message)
            assert telegram.messages[-2].text.startswith("COMUNICAZIONE DEGLI ADMIN SUL TUO ULTIMO REPORT:\n")
            assert telegram.messages[-2].text.endswith("TEST")
            assert telegram.last_message.text.startswith("L'utente ha ricevuto il seguente messaggio:\n")
            assert telegram.last_message.text.endswith("TEST")

        def test_reply_report_spot_cmd(self, telegram: TelegramSimulator, admin_group: Chat, report_spot_message: Message):
            """Tests the /reply command.
            The bot sends a message to the user on behalf of the admin
            """
            group_message, _ = report_spot_message
            telegram.send_message("/reply TEST", chat=admin_group, reply_to_message=group_message)
            assert telegram.messages[-2].text.startswith("COMUNICAZIONE DEGLI ADMIN SUL TUO ULTIMO REPORT:\n")
            assert telegram.messages[-2].text.endswith("TEST")
            assert telegram.last_message.text.startswith("L'utente ha ricevuto il seguente messaggio:\n")
            assert telegram.last_message.text.endswith("TEST")

        def test_clean_pending(self, telegram: TelegramSimulator, admin_group: Chat):
            """Tests the /clean_pending command.
            The bot cleans the old pending posts, while ignoring the more recent ones
            """
            # An old an a recent pending posts are present
            PendingPost(1, 1, 1, config_map['meme']['group_id'], datetime.fromtimestamp(1)).save_post()
            PendingPost(2, 2, 2, config_map['meme']['group_id'], datetime.now()).save_post()
            telegram.send_command("/clean_pending", chat=admin_group)
            assert telegram.messages[
                -2].text == "Gli admin erano sicuramente molto impegnati e non sono riusciti a valutare lo spot in tempo"
            assert telegram.last_message.text == "Sono stati eliminati 1 messaggi rimasti in sospeso"
            assert PendingPost.from_user(1) is None
            assert PendingPost.from_user(2) is not None

    class TestBotSpotConversation:
        """Tests the spot conversation"""

        def test_spot_no_private_cmd(self, telegram: TelegramSimulator, channel_group: Chat):
            """Tests the /spot command.
            Spot is not allowed in groups
            """
            telegram.send_command("/spot", chat=channel_group)
            assert telegram.last_message.text == CHAT_PRIVATE_ERROR

        def test_spot_banned_cmd(self, telegram: TelegramSimulator):
            """Tests the /spot command.
            Spot is not allowed for banned users
            """
            User(1).ban()  # by default the user used by the telegram simulator has id 1
            telegram.send_command("/spot")
            assert telegram.last_message.text == "Sei stato bannato 😅"

        def test_spot_pending_cmd(self, telegram: TelegramSimulator, local_table):
            """Tests the /spot command.
            Spot is not allowed for users with a pending post
            """
            PendingPost(user_id=1, u_message_id=1, g_message_id=1, group_id=1, date=datetime.now()).save_post()
            telegram.send_command("/spot")
            assert telegram.last_message.text == "Hai già un post in approvazione 🧐"

        def test_spot_cancel_cmd(self, telegram: TelegramSimulator):
            """Tests the /spot command.
            Cancel spot conversation
            """
            telegram.send_command("/spot")
            assert telegram.last_message.text == "Invia il post che vuoi pubblicare"

            telegram.send_command("/cancel")
            assert telegram.last_message.text == read_md("spot_cancel")

            telegram.send_command("/spot")
            assert telegram.last_message.text == "Invia il post che vuoi pubblicare"

        def test_spot_no_cmd(self, telegram: TelegramSimulator):
            """Tests the /spot command.
            Complete with no the spot conversation
            """
            telegram.send_command("/spot")
            assert telegram.last_message.text == "Invia il post che vuoi pubblicare"

            telegram.send_message("Test spot")
            assert telegram.last_message.text == "Sei sicuro di voler publicare questo post?"
            assert telegram.last_message.reply_to_message is not None

            telegram.send_callback_query(text="No")
            assert telegram.last_message.text == "Va bene, alla prossima 🙃"

            telegram.send_command("/spot")
            assert telegram.last_message.text == "Invia il post che vuoi pubblicare"

        def test_spot_si_cmd(self, telegram: TelegramSimulator):
            """Tests the /spot command.
            Complete with yes the spot conversation
            """
            telegram.send_command("/spot")
            assert telegram.last_message.text == "Invia il post che vuoi pubblicare"

            telegram.send_message("Test spot")
            assert telegram.last_message.text == "Sei sicuro di voler publicare questo post?"
            assert telegram.last_message.reply_to_message is not None

            telegram.send_callback_query(text="Si")
            assert telegram.last_message.text == "Il tuo post è in fase di valutazione\n"\
                f"Una volta pubblicato, lo potrai trovare su {config_map['meme']['channel_tag']}"

            telegram.send_command("/spot")
            assert telegram.last_message.text == "Hai già un post in approvazione 🧐"

            PendingPost.from_user(1).delete_post()
            telegram.send_command("/spot")
            assert telegram.last_message.text == "Invia il post che vuoi pubblicare"

    class TestBotSettings:
        """Tests the settings commands"""

        def test_settings_cmd(self, telegram: TelegramSimulator):
            """Tests the /settings command.
            The bot sends the settings response to the user
            """
            telegram.send_command("/settings")
            assert telegram.last_message.text == "***Come vuoi che sia il tuo post:***"

        def test_settings_anonym_from_anonym_cmd(self, telegram: TelegramSimulator):
            """Tests the /settings command.
            The user becomes anonym already being anonym
            """
            telegram.send_command("/settings")
            assert telegram.last_message.text == "***Come vuoi che sia il tuo post:***"

            telegram.send_callback_query(text=" Anonimo ")
            assert telegram.last_message.text == "Sei già anonimo"

            assert not User(1).is_credited

        def test_settings_anonym_from_credited_cmd(self, telegram: TelegramSimulator):
            """Tests the /settings command.
            The user becomes anonym from being credited
            """
            User(1).become_credited()
            telegram.send_command("/settings")
            assert telegram.last_message.text == "***Come vuoi che sia il tuo post:***"

            telegram.send_callback_query(text=" Anonimo ")
            assert telegram.last_message.text == "La tua preferenza è stata aggiornata\n"\
                                                    "Ora i tuoi post saranno anonimi"
            assert not User(1).is_credited

        def test_settings_credited_from_anonym_cmd(self, telegram: TelegramSimulator):
            """Tests the /settings command.
            The user becomes credited from being anonym
            """
            telegram.send_command("/settings")
            assert telegram.last_message.text == "***Come vuoi che sia il tuo post:***"

            telegram.send_callback_query(text=" Con credit ")
            assert telegram.last_message.text == "La tua preferenza è stata aggiornata\n"\
                                                    f"I tuoi post avranno come credit @{telegram.user.username}"

            assert User(1).is_credited

        def test_settings_credited_from_credited_cmd(self, telegram: TelegramSimulator):
            """Tests the /settings command.
            The user becomes credited already being credited
            """
            User(1).become_credited()
            telegram.send_command("/settings")
            assert telegram.last_message.text == "***Come vuoi che sia il tuo post:***"

            telegram.send_callback_query(text=" Con credit ")
            assert telegram.last_message.text == "Sei già creditato nei post\n"\
                                                    f"I tuoi post avranno come credit @{telegram.user.username}"

            assert User(1).is_credited

    class TestReportUser:
        """Tests the report user commands"""

        def test_report_user_invalid_username_cmd(self, telegram: TelegramSimulator):
            """Tests the /report user command.
            The username submitted is not a valid Telegram username
            """
            telegram.send_command("/report")
            assert telegram.last_message.text == "Invia l'username di chi vuoi segnalare. Es. @massimobene"

            telegram.send_message("massimobene")
            assert telegram.last_message.text.startswith("Questo tipo di messaggio non è supportato\n")

            telegram.send_message("@massimo bene")
            assert telegram.last_message.text.startswith("Questo tipo di messaggio non è supportato\n")

        def test_report_user_cmd(self, telegram: TelegramSimulator):
            """Tests the /report user command.
            The bot sends the report from the user to the admins
            """
            telegram.send_command("/report")
            assert telegram.last_message.text == "Invia l'username di chi vuoi segnalare. Es. @massimobene"

            telegram.send_message("@massimobene")
            assert telegram.last_message.text.startswith("Scrivi il motivo della tua segnalazione.\n")

            telegram.send_message("Motivo segnalazione")

            assert telegram.messages[-2].text.startswith("🚨🚨 SEGNALAZIONE 🚨🚨\n\n")
            assert telegram.last_message.text == "Gli admins verificheranno quanto accaduto. Grazie per la collaborazione!"
            assert Report.get_last_user_report(telegram.user.id) is not None

        def test_report_user_cooldown_cmd(self, telegram: TelegramSimulator):
            """Tests the /report user command's cooldown timer.
            The user cannot report again for the amount of time enstablished in the settings
            """
            telegram.send_command("/report")
            assert telegram.last_message.text == "Invia l'username di chi vuoi segnalare. Es. @massimobene"

            telegram.send_message("@massimobene")
            assert telegram.last_message.text.startswith("Scrivi il motivo della tua segnalazione.\n")

            telegram.send_message("Motivo segnalazione")

            assert telegram.messages[-2].text.startswith("🚨🚨 SEGNALAZIONE 🚨🚨\n\n")
            assert telegram.last_message.text == "Gli admins verificheranno quanto accaduto. Grazie per la collaborazione!"
            assert Report.get_last_user_report(telegram.user.id) is not None

            telegram.send_command("/report")
            assert telegram.last_message.text == f"Aspetta {config_map['meme']['report_wait_mins'] - 1} minuti"

    class TestReportSpot:
        """Tests the report spot commands"""

        def test_report_post_query(self, telegram: TelegramSimulator, published_post_message: Message):
            """Tests the /report user query.
            The user successfully reports a post already published in the channel
            """
            telegram.send_callback_query(data="meme_report_spot,", message=published_post_message)
            assert telegram.last_message.text == "Scrivi il motivo della segnalazione del post, altrimenti digita /cancel"

            telegram.send_message("Motivo segnalazione")
            assert telegram.messages[-2].text.startswith("🚨🚨 SEGNALAZIONE 🚨🚨\n\n")
            assert telegram.last_message.text == "Gli admins verificheranno quanto accaduto. Grazie per la collaborazione!"
            assert Report.get_post_report(telegram.user.id, published_post_message.chat_id,
                                          published_post_message.reply_to_message.message_id) is not None

        def test_report_post_again_query(self, telegram: TelegramSimulator, published_post_message: Message):
            """Tests the /report user query.
            The user cannot report again a post already published in the channel
            """
            telegram.send_callback_query(data="meme_report_spot,", message=published_post_message)
            assert telegram.last_message.text == "Scrivi il motivo della segnalazione del post, altrimenti digita /cancel"

            telegram.send_message("Motivo segnalazione")
            assert telegram.messages[-2].text.startswith("🚨🚨 SEGNALAZIONE 🚨🚨\n\n")
            assert telegram.last_message.text == "Gli admins verificheranno quanto accaduto. Grazie per la collaborazione!"
            assert Report.get_post_report(telegram.user.id, published_post_message.chat_id,
                                          published_post_message.reply_to_message.message_id) is not None

            telegram.send_callback_query(data="meme_report_spot,", message=published_post_message)
            # The next message is the same as the last, because if the user try to report again
            # the query will be answered with a warning but no new messages will be sent by the bot
            assert telegram.last_message.text == "Gli admins verificheranno quanto accaduto. Grazie per la collaborazione!"
