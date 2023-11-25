# pylint: disable=unused-argument,redefined-outer-name
"""Tests the bot functionality"""
import os
from datetime import datetime

import pytest
import pytest_asyncio
from telegram import Chat, Message, MessageEntity
from telegram import User as TGUser
from telegram_simulator import TelegramSimulator

from spotted.data import (
    Config,
    DbManager,
    PendingPost,
    PublishedPost,
    Report,
    User,
    read_md,
)
from spotted.utils.constants import APPROVED_KB, REJECTED_KB


@pytest.fixture(scope="function")
def telegram(test_table: DbManager) -> TelegramSimulator:
    """Called once per at the beginning of each function.
    Creates a telegram simulator object

    Returns:
        telegram weaver
    """
    return TelegramSimulator()


async def pending_post(telegram: TelegramSimulator, user: TGUser) -> Message:
    """Called once per at the beginning of each function.
    Simulates an existing pending post

    Returns:
        pending post message
    """
    await telegram.send_command("/spot", user=user)
    await telegram.send_message("Test spot", user=user)
    await telegram.send_callback_query(text="Si", user=user)
    return telegram.last_message


@pytest_asyncio.fixture(scope="function", name="pending_post")
async def pending_post_fixture(telegram: TelegramSimulator, user: TGUser) -> Message:
    """Called once per at the beginning of each function.
    Simulates an existing pending post

    Returns:
        pending post message
    """
    return await pending_post(telegram, user)


async def published_post(telegram: TelegramSimulator, channel: Chat, channel_group: Chat) -> Message:
    """Called once per at the beginning of each function.
    Simulates an existing published post

    Returns:
        published post message
    """
    for i in range(Config.post_get("n_votes")):
        await telegram.send_callback_query(
            text=f"🟢 {i}", message=telegram.last_message, user=TGUser(i + 1, first_name=str(i), is_bot=False)
        )
    if Config.post_get("comments"):
        await telegram.send_forward_message(
            forward_message=telegram.messages[-2],
            chat=channel_group,
            is_automatic_forward=True,
            user=TGUser(1, first_name="Telegram", is_bot=False),
        )
        assert PublishedPost.from_channel(channel_group.id, telegram.last_message.message_id)
        return telegram.last_message

    assert PublishedPost.from_channel(channel.id, telegram.messages[-2].message_id)
    return telegram.messages[-2]


@pytest_asyncio.fixture(scope="function", name="published_post")
async def published_post_fixture(
    telegram: TelegramSimulator, pending_post: Message, channel: Chat, channel_group: Chat
) -> Message:
    """Called once per at the beginning of each function.
    Simulates an existing published post

    Returns:
        published post message
    """
    return await published_post(telegram, channel, channel_group)


@pytest.fixture(scope="function")
def report_user_message(telegram: TelegramSimulator, user: TGUser, admin_group: Chat, channel: Chat) -> Message:
    """Called once per at the beginning of each function.
    Simulates an existing user report

    Returns:
        user report message
    """
    r_message = telegram.make_message("Report user", chat=admin_group)
    telegram.add_message(r_message)
    Report(user.id, admin_group.id, r_message.id, target_username="BadUser", date=datetime.now()).save_report()
    return r_message


@pytest.fixture(scope="function")
def report_spot_message(
    telegram: TelegramSimulator, user: TGUser, admin_group: Chat, channel: Chat
) -> tuple[Message, Message]:
    """Called once per at the beginning of each function.
    Simulates an existing spot report

    Returns:
        spot report in the admin group and post in the channel
    """
    c_message = telegram.make_message("Bad spot", chat=channel)
    r_message = telegram.make_message("Report spot", chat=admin_group)
    telegram.add_message(c_message)
    telegram.add_message(r_message)
    Report(
        user.id,
        admin_group.id,
        r_message.id,
        channel_id=channel.id,
        c_message_id=c_message.message_id,
        date=datetime.now(),
    ).save_report()
    return r_message, c_message


@pytest.fixture(scope="class")
def user() -> TGUser:
    """Called once per at the beginning of each class.
    Returns the user

    Returns:
        user
    """
    return TGUser(id=1, first_name="User", is_bot=False, username="user")


@pytest.fixture(scope="class")
def user_chat(user: TGUser) -> Chat:
    """Called once per at the beginning of each class.
    Returns the private chat with the user

    Returns:
        private chat with the user
    """
    return Chat(id=user.id, type=Chat.PRIVATE)


@pytest.fixture(scope="class")
def channel() -> Chat:
    """Called once per at the beginning of each class.
    Returns the channel chat

    Returns:
        channel chat
    """
    return Chat(id=Config.post_get("channel_id"), type=Chat.CHANNEL)


@pytest.fixture(scope="class")
def admin_group() -> Chat:
    """Called once per at the beginning of each class.
    Returns the admin group chat

    Returns:
        admin group chat
    """
    return Chat(id=Config.post_get("admin_group_id"), type=Chat.GROUP)


@pytest.fixture(scope="class")
def channel_group() -> Chat:
    """Called once per at the beginning of each class.
    Returns the chat of the public group with the comments

    Returns:
        public group for comments
    """
    return Chat(id=Config.post_get("community_group_id"), type=Chat.GROUP)


@pytest.mark.asyncio
class TestBot:
    """Tests the bot simulating the telegram API's responses"""

    class TestBotBasicCommand:
        """Tests the bot commands"""

        async def test_start_cmd(self, telegram: TelegramSimulator):
            """Tests the /start command.
            The bot sends the start response to the user
            """
            await telegram.send_command("/start")
            assert telegram.last_message.text == read_md("start")

        async def test_help_user_cmd(self, telegram: TelegramSimulator):
            """Tests the /help command.
            The bot sends the help response to the user
            """
            await telegram.send_command("/help")
            assert telegram.last_message.text == read_md("help")

        async def test_help_admin_cmd(self, telegram: TelegramSimulator, admin_group: Chat):
            """Tests the /help command.
            The bot sends the help response to the admins
            """
            await telegram.send_command("/help", chat=admin_group)
            assert telegram.last_message.text == read_md("instructions")

        async def test_rules_cmd(self, telegram: TelegramSimulator):
            """Tests the /rules command.
            The bot sends the rules response to the user
            """
            await telegram.send_command("/rules")
            assert telegram.last_message.text == read_md("rules")

    class TestBotAdminCommand:
        """Tests the bot commands reserved for admins"""

        async def test_ban_cmd(self, telegram: TelegramSimulator, admin_group: Chat, pending_post: Message):
            """Tests the /ban command.
            The bot bans the user associated with the pending post
            """
            await telegram.send_message("/ban", chat=admin_group, reply_to_message=pending_post)
            assert telegram.last_message.text == "L'utente è stato bannato"
            assert PendingPost.from_group(pending_post.message_id, pending_post.chat_id) is None
            assert User(1).is_banned

        async def test_sban_invalid_cmd(self, telegram: TelegramSimulator, admin_group: Chat):
            """Tests the /sban command.
            The bot warns about invalid command
            """
            await telegram.send_command("/sban", chat=admin_group)
            assert (
                telegram.last_message.text == "[uso]: /sban <user_id1> [...user_id2]\n"
                "Gli utenti attualmente bannati sono:\n"
                "Nessuno"
            )

        async def test_sban_list_invalid_cmd(self, telegram: TelegramSimulator, admin_group: Chat):
            """Tests the /sban command.
            The bot warns about invalid command
            """
            User(5).ban()  # the user 5 and 6 have been banned
            User(6).ban()
            ban_date = datetime.now()  # to make sure no weird stuff happens with the date
            DbManager.update_from(table_name="banned_users", set_clause="ban_date=%s", args=(ban_date,))
            await telegram.send_command("/sban", chat=admin_group)
            assert (
                telegram.last_message.text == "[uso]: /sban <user_id1> [...user_id2]\n"
                "Gli utenti attualmente bannati sono:\n"
                f"5 ({ban_date:%d/%m/%Y %H:%M})\n"
                f"6 ({ban_date:%d/%m/%Y %H:%M})"  # list the banned users
            )

        async def test_sban_cmd(self, telegram: TelegramSimulator, admin_group: Chat):
            """Tests the /sban command.
            The bot sbans the users specified user
            """
            User(1).ban()
            await telegram.send_command("/sban 1", chat=admin_group)
            assert telegram.last_message.text == "Sban effettuato"
            assert not User(1).is_banned

        async def test_reply_invalid_cmd(self, telegram: TelegramSimulator, admin_group: Chat, pending_post: Message):
            """Tests the /reply command.
            The bot warns about invalid command
            """
            await telegram.send_message("/reply", chat=admin_group, reply_to_message=pending_post)
            assert telegram.last_message.text.startswith("La reply è vuota\n")

        async def test_reply_post_cmd(self, telegram: TelegramSimulator, admin_group: Chat, pending_post: Message):
            """Tests the /reply command.
            The bot sends a message to the user on behalf of the admin
            """
            await telegram.send_message("/reply TEST", chat=admin_group, reply_to_message=pending_post)
            assert telegram.messages[-2].text.startswith("COMUNICAZIONE DEGLI ADMIN SUL TUO ULTIMO POST:\n")
            assert telegram.messages[-2].text.endswith("TEST")
            assert telegram.last_message.text == "L'utente ha ricevuto il messaggio"

        async def test_autoreply_list_cmd(self, telegram: TelegramSimulator, admin_group: Chat, pending_post: Message):
            """Tests the /autoreply command.
            Show the admins all the possible arguments for the autoreply command
            """
            await telegram.send_command("/autoreply list", chat=admin_group, reply_to_message=pending_post)
            possible_args_text = "\n - ".join(Config.autoreplies_get("autoreplies").keys())
            assert telegram.last_message.text == f"Possibili argomenti:\n - {possible_args_text}"

        @pytest.mark.parametrize("autoreply", Config.autoreplies_get("autoreplies").keys())
        async def test_autoreply_invalid_cmd(self, telegram: TelegramSimulator, admin_group: Chat, autoreply: str):
            """Tests the /autoreply command.
            The autoreply command can only be submitted by replying to a pending post or report
            """
            await telegram.send_message("Random message")
            await telegram.send_command(
                f"/autoreply {autoreply}", chat=admin_group, reply_to_message=telegram.last_message
            )
            assert telegram.last_message.text.startswith("Il messaggio selezionato non è valido")

        @pytest.mark.parametrize("autoreply", Config.autoreplies_get("autoreplies").keys())
        async def test_autoreply_cmd(
            self, telegram: TelegramSimulator, admin_group: Chat, pending_post: Message, autoreply: str
        ):
            """Tests the /autoreply command.
            The admins can send a reply to the user with an automatic message
            """
            await telegram.send_message(f"/autoreply {autoreply}", chat=admin_group, reply_to_message=pending_post)
            assert telegram.messages[-2].text.endswith(Config.autoreplies_get("autoreplies")[autoreply])
            assert telegram.last_message.text == "L'utente ha ricevuto il messaggio"

        async def test_reply_report_user_cmd(
            self, telegram: TelegramSimulator, admin_group: Chat, report_user_message: Message
        ):
            """Tests the /reply command.
            The bot sends a message to the user on behalf of the admin
            """
            await telegram.send_message("/reply TEST", chat=admin_group, reply_to_message=report_user_message)
            assert telegram.messages[-2].text.startswith("COMUNICAZIONE DEGLI ADMIN SUL TUO ULTIMO REPORT:\n")
            assert telegram.messages[-2].text.endswith("TEST")
            assert telegram.last_message.text == "L'utente ha ricevuto il messaggio"

        async def test_reply_report_spot_cmd(
            self, telegram: TelegramSimulator, admin_group: Chat, report_spot_message: Message
        ):
            """Tests the /reply command.
            The bot sends a message to the user on behalf of the admin
            """
            group_message, _ = report_spot_message
            await telegram.send_message("/reply TEST", chat=admin_group, reply_to_message=group_message)
            assert telegram.messages[-2].text.startswith("COMUNICAZIONE DEGLI ADMIN SUL TUO ULTIMO REPORT:\n")
            assert telegram.messages[-2].text.endswith("TEST")
            assert telegram.last_message.text == "L'utente ha ricevuto il messaggio"

        async def test_clean_pending(
            self, test_table: DbManager, telegram: TelegramSimulator, admin_group: Chat, user: TGUser
        ):
            """Tests the /clean_pending command.
            The bot cleans the old pending posts, while ignoring the more recent ones
            """
            user2 = TGUser(2, first_name="User2", is_bot=False, username="user2")
            _ = await pending_post(telegram, user=user)
            g_message2 = await pending_post(telegram, user=user2)
            test_table.update_from(
                "pending_post", "message_date=%s", "g_message_id=%s", (datetime.fromtimestamp(1), g_message2.message_id)
            )
            await telegram.send_command("/clean_pending", chat=admin_group)
            assert (
                telegram.messages[-2].text
                == "Gli admin erano sicuramente molto impegnati e non sono riusciti a valutare lo spot in tempo"
            )
            assert telegram.last_message.text == "Sono stati eliminati 1 messaggi rimasti in sospeso"
            assert PendingPost.from_user(user.id) is not None  # the recent pending post has not been deleted
            assert PendingPost.from_user(user2.id) is None  # the old pending post has been deleted

        async def test_reload_cmd(self, telegram: TelegramSimulator, admin_group: Chat):
            """Tests the /reload command.
            The bot reloads the settings
            """
            os.environ["BOT_TAG"] = "test_reload_cmd"
            await telegram.send_command("/reload", chat=admin_group)
            assert telegram.last_message.text == "Configurazione ricaricata"
            assert Config.settings_get("bot_tag") == "test_reload_cmd"
            del os.environ["BOT_TAG"]

    class TestBotSpotConversation:
        """Tests the spot conversation"""

        async def test_spot_no_private_cmd(self, telegram: TelegramSimulator, channel_group: Chat):
            """Tests the /spot command.
            Spot is not allowed in groups
            """
            await telegram.send_command("/spot", chat=channel_group)
            assert telegram.last_message.text == "/spot"  # the bot does not reply to the command

        async def test_spot_banned_cmd(self, telegram: TelegramSimulator):
            """Tests the /spot command.
            Spot is not allowed for banned users
            """
            User(1).ban()  # by default the user used by the telegram simulator has id 1
            await telegram.send_command("/spot")
            assert telegram.last_message.text == "Sei stato bannato 😅"

        async def test_spot_pending_cmd(self, telegram: TelegramSimulator):
            """Tests the /spot command.
            Spot is not allowed for users with a pending post
            """
            PendingPost(user_id=1, u_message_id=1, g_message_id=1, admin_group_id=1, date=datetime.now()).save_post()
            await telegram.send_command("/spot")
            assert telegram.last_message.text == "Hai già un post in approvazione 🧐"

        async def test_spot_cancel_cmd(self, telegram: TelegramSimulator):
            """Tests the /spot command.
            Cancel spot conversation
            """
            await telegram.send_command("/spot")
            assert telegram.last_message.text == "Invia il post che vuoi pubblicare"

            await telegram.send_command("/cancel")
            assert telegram.last_message.text == read_md("spot_cancel")

            await telegram.send_command("/spot")
            assert telegram.last_message.text == "Invia il post che vuoi pubblicare"

        async def test_spot_no_cmd(self, telegram: TelegramSimulator):
            """Tests the /spot command.
            Complete with no the spot conversation
            """
            await telegram.send_command("/spot")
            assert telegram.last_message.text == "Invia il post che vuoi pubblicare"

            await telegram.send_message("Test spot")
            assert telegram.last_message.text == "Sei sicuro di voler pubblicare questo post?"
            assert telegram.last_message.reply_to_message is not None

            await telegram.send_callback_query(text="No")
            assert telegram.last_message.text in read_md("no_strings").split("\n")

            await telegram.send_command("/spot")
            assert telegram.last_message.text == "Invia il post che vuoi pubblicare"

        async def test_spot_si_cmd(self, telegram: TelegramSimulator):
            """Tests the /spot command.
            Complete with yes the spot conversation
            """
            await telegram.send_command("/spot")
            assert telegram.last_message.text == "Invia il post che vuoi pubblicare"

            await telegram.send_message("Test spot")
            assert telegram.last_message.text == "Sei sicuro di voler pubblicare questo post?"
            assert telegram.last_message.reply_to_message is not None

            await telegram.send_callback_query(text="Si")
            assert (
                telegram.messages[-2].text == "Il tuo post è in fase di valutazione\n"
                f"Una volta pubblicato, lo potrai trovare su {Config.post_get('channel_tag')}"
            )

            await telegram.send_command("/spot")
            assert telegram.last_message.text == "Hai già un post in approvazione 🧐"

            PendingPost.from_user(1).delete_post()
            await telegram.send_command("/spot")
            assert telegram.last_message.text == "Invia il post che vuoi pubblicare"

        async def test_spot_link_cmd(self, telegram: TelegramSimulator):
            """Tests the /spot command.
            Send spot with a link
            """
            await telegram.send_command("/spot")
            assert telegram.last_message.text == "Invia il post che vuoi pubblicare"

            await telegram.send_message(
                "Hai vinto un iPad 🎉",
                entities=[
                    MessageEntity(
                        type=MessageEntity.URL, offset=0, length=19, url="https://www.youtube.com/watch?v=dQw4w9WgXcQ"
                    )
                ],
            )

            assert telegram.last_message.text == "Il post contiene link, vuoi pubblicare con l'anteprima?"

        async def test_spot_link_with_preview_cmd(self, telegram: TelegramSimulator):
            """Tests the /spot command.
            Send spot with a link with preview and complete the conversation
            """
            await self.test_spot_link_cmd(telegram)
            await telegram.send_callback_query(text="Si")

            assert telegram.last_message.text == "Sei sicuro di voler pubblicare questo post?"

        async def test_spot_link_without_preview_cmd(self, telegram: TelegramSimulator):
            """Tests the /spot command.
            Send spot with a link with preview and complete the conversation
            """
            await self.test_spot_link_cmd(telegram)
            await telegram.send_callback_query(text="No")

            assert telegram.last_message.text == "Sei sicuro di voler pubblicare questo post?"

    class TestBotSettings:
        """Tests the settings commands"""

        async def test_settings_cmd(self, telegram: TelegramSimulator):
            """Tests the /settings command.
            The bot sends the settings response to the user
            """
            await telegram.send_command("/settings")
            assert telegram.last_message.text == "***Come vuoi che sia il tuo post:***"

        async def test_settings_anonym_from_anonym_cmd(self, telegram: TelegramSimulator):
            """Tests the /settings command.
            The user becomes anonym already being anonym
            """
            await telegram.send_command("/settings")
            assert telegram.last_message.text == "***Come vuoi che sia il tuo post:***"

            await telegram.send_callback_query(text=" Anonimo ")
            assert telegram.last_message.text == "Sei già anonimo"

            assert not User(1).is_credited

        async def test_settings_anonym_from_credited_cmd(self, telegram: TelegramSimulator):
            """Tests the /settings command.
            The user becomes anonym from being credited
            """
            User(1).become_credited()
            await telegram.send_command("/settings")
            assert telegram.last_message.text == "***Come vuoi che sia il tuo post:***"

            await telegram.send_callback_query(text=" Anonimo ")
            assert (
                telegram.last_message.text == "La tua preferenza è stata aggiornata\n" "Ora i tuoi post saranno anonimi"
            )
            assert not User(1).is_credited

        async def test_settings_credited_from_anonym_cmd(self, telegram: TelegramSimulator, user: TGUser):
            """Tests the /settings command.
            The user becomes credited from being anonym
            """
            await telegram.send_command("/settings", user=user)
            assert telegram.last_message.text == "***Come vuoi che sia il tuo post:***"

            await telegram.send_callback_query(text=" Con credit ", user=user)
            assert (
                telegram.last_message.text == "La tua preferenza è stata aggiornata\n"
                f"I tuoi post avranno come credit @{user.username}"
            )

            assert User(1).is_credited

        async def test_settings_credited_from_credited_cmd(self, telegram: TelegramSimulator, user: TGUser):
            """Tests the /settings command.
            The user becomes credited already being credited
            """
            User(1).become_credited()
            await telegram.send_command("/settings", user=user)
            assert telegram.last_message.text == "***Come vuoi che sia il tuo post:***"

            await telegram.send_callback_query(text=" Con credit ", user=user)
            assert (
                telegram.last_message.text == "Sei già creditato nei post\n"
                f"I tuoi post avranno come credit @{user.username}"
            )

            assert User(1).is_credited

    class TestReportUser:
        """Tests the report user commands"""

        async def test_report_user_invalid_username_cmd(self, telegram: TelegramSimulator):
            """Tests the /report user command.
            The username submitted is not a valid Telegram username
            """
            await telegram.send_command("/report")
            assert telegram.last_message.text == "Invia l'username di chi vuoi segnalare. Es. @massimobene"

            await telegram.send_message("massimobene")
            assert telegram.last_message.text.startswith("Questo tipo di messaggio non è supportato\n")

            await telegram.send_message("@massimo bene")
            assert telegram.last_message.text.startswith("Questo tipo di messaggio non è supportato\n")

        async def test_report_user_cmd(self, telegram: TelegramSimulator):
            """Tests the /report user command.
            The bot sends the report from the user to the admins
            """
            await telegram.send_command("/report")
            assert telegram.last_message.text == "Invia l'username di chi vuoi segnalare. Es. @massimobene"

            await telegram.send_message("@massimobene")
            assert telegram.last_message.text.startswith("Scrivi il motivo della tua segnalazione.\n")

            await telegram.send_message("Motivo segnalazione")

            assert telegram.messages[-2].text.startswith("🚨🚨 SEGNALAZIONE 🚨🚨\n\n")
            assert (
                telegram.last_message.text == "Gli admins verificheranno quanto accaduto. Grazie per la collaborazione!"
            )
            assert Report.get_last_user_report(telegram.user.id) is not None

        async def test_report_user_cooldown_cmd(self, telegram: TelegramSimulator):
            """Tests the /report user command's cooldown timer.
            The user cannot report again for the amount of time established in the settings
            """
            await telegram.send_command("/report")
            assert telegram.last_message.text == "Invia l'username di chi vuoi segnalare. Es. @massimobene"

            await telegram.send_message("@massimobene")
            assert telegram.last_message.text.startswith("Scrivi il motivo della tua segnalazione.\n")

            await telegram.send_message("Motivo segnalazione")

            assert telegram.messages[-2].text.startswith("🚨🚨 SEGNALAZIONE 🚨🚨\n\n")
            assert (
                telegram.last_message.text == "Gli admins verificheranno quanto accaduto. Grazie per la collaborazione!"
            )
            assert Report.get_last_user_report(telegram.user.id) is not None

            await telegram.send_command("/report")
            assert telegram.last_message.text == f"Aspetta {Config.post_get('report_wait_mins') - 1} minuti"

    class TestReportSpot:
        """Tests the report spot commands"""

        async def test_report_post_query(self, telegram: TelegramSimulator, published_post: Message):
            """Tests the /report user query.
            The user successfully reports a post already published in the channel
            """
            await telegram.send_callback_query(data="report_spot,", message=published_post)
            assert (
                telegram.last_message.text == "Scrivi il motivo della segnalazione del post, altrimenti digita /cancel"
            )

            await telegram.send_message("Motivo segnalazione")
            assert telegram.messages[-2].text.startswith("🚨🚨 SEGNALAZIONE 🚨🚨\n\n")
            assert (
                telegram.last_message.text == "Gli admins verificheranno quanto accaduto. Grazie per la collaborazione!"
            )
            assert (
                Report.get_post_report(
                    telegram.user.id, published_post.chat_id, published_post.reply_to_message.message_id
                )
                is not None
            )

        async def test_report_post_again_query(self, telegram: TelegramSimulator, published_post: Message):
            """Tests the /report user query.
            The user cannot report again a post already published in the channel
            """
            await telegram.send_callback_query(data="report_spot,", message=published_post)
            assert (
                telegram.last_message.text == "Scrivi il motivo della segnalazione del post, altrimenti digita /cancel"
            )

            await telegram.send_message("Motivo segnalazione")
            assert telegram.messages[-2].text.startswith("🚨🚨 SEGNALAZIONE 🚨🚨\n\n")
            assert (
                telegram.last_message.text == "Gli admins verificheranno quanto accaduto. Grazie per la collaborazione!"
            )
            assert (
                Report.get_post_report(
                    telegram.user.id, published_post.chat_id, published_post.reply_to_message.message_id
                )
                is not None
            )

            await telegram.send_callback_query(data="report_spot,", message=published_post)
            # The next message is the same as the last, because if the user try to report again
            # the query will be answered with a warning but no new messages will be sent by the bot
            assert (
                telegram.last_message.text == "Gli admins verificheranno quanto accaduto. Grazie per la collaborazione!"
            )

    class TestSpotLinkPreview:
        """Test the spot link preview"""

        async def test_spot_link(self, telegram: TelegramSimulator):
            """Tests the /spot command.
            Send spot with a link
            """
            await telegram.send_command("/spot")
            assert telegram.last_message.text == "Invia il post che vuoi pubblicare"

            await telegram.send_message(
                "Hai vinto un iPad 🎉",
                entities=[
                    MessageEntity(
                        type=MessageEntity.URL, offset=0, length=19, url="https://www.youtube.com/watch?v=dQw4w9WgXcQ"
                    )
                ],
            )

            assert telegram.last_message.text == "Il post contiene link, vuoi pubblicare con l'anteprima?"
            assert telegram.last_message.reply_to_message is not None

        async def test_spot_link_with_preview(self, telegram: TelegramSimulator):
            """Tests the /spot command.
            Complete with yes the spot with link preview conversation
            """
            await self.test_spot_link(telegram)

            await telegram.send_callback_query(text="Si")
            assert telegram.last_message.text == "Sei sicuro di voler pubblicare questo post?"

            # The last edited message will not have the reply_to_message attribute (because of bot APIs)
            # So instead we use the original message (the one that was sent before the callback query)
            # and specify the data of the callback query manually
            await telegram.send_callback_query(data="post_confirm,submit", message=telegram.last_message)
            types = [entity.type for entity in telegram.last_message.entities]
            assert MessageEntity.URL in types

        async def test_spot_link_without_preview(self, telegram: TelegramSimulator):
            """Tests the /spot command.
            Complete with no the spot without link preview conversation
            """
            await self.test_spot_link(telegram)

            await telegram.send_callback_query(text="No")
            assert telegram.last_message.text == "Sei sicuro di voler pubblicare questo post?"

            await telegram.send_callback_query(data="post_confirm,submit", message=telegram.last_message)
            types = [entity.type for entity in telegram.last_message.entities]
            assert MessageEntity.URL in types
            # NOTE: There is no way to check if message has preview

    class TestPublishSpot:
        """Tests the complete publishing spot pipeline"""

        async def test_spot_pipeline(
            self, telegram: TelegramSimulator, user: TGUser, admin_group: Chat, channel: Chat, channel_group: Chat
        ):
            """Tests the /spot command.
            Complete with yes the spot conversation
            """
            await telegram.send_command("/spot")
            assert telegram.last_message.text == "Invia il post che vuoi pubblicare"

            await telegram.send_message("Test spot")
            assert telegram.last_message.text == "Sei sicuro di voler pubblicare questo post?"
            assert telegram.last_message.reply_to_message is not None

            await telegram.send_callback_query(text="Si")

            assert telegram.last_message.text == "Test spot"
            assert (
                telegram.messages[-2].text == "Il tuo post è in fase di valutazione\n"
                f"Una volta pubblicato, lo potrai trovare su {Config.post_get('channel_tag')}"
            )
            assert (
                PendingPost.from_group(g_message_id=telegram.last_message.message_id, admin_group_id=admin_group.id)
                is not None
            )

            user2 = TGUser(2, first_name="Test2", is_bot=False)
            await telegram.send_callback_query(text="🟢 0", message=telegram.last_message)
            await telegram.send_callback_query(text="🟢 1", message=telegram.last_message, user=user2)

            g_message = telegram.messages[-3]
            assert g_message.reply_markup.inline_keyboard[0][0].text == f"🟢 @{user.id}"
            assert g_message.reply_markup.inline_keyboard[1][0].text == f"🟢 @{user2.id}"
            assert g_message.reply_markup.inline_keyboard[2][0].text == APPROVED_KB
            assert telegram.last_message.text.startswith("Il tuo ultimo post è stato pubblicato")

            c_message = telegram.messages[-2]
            assert c_message.text == "Test spot"

            assert PendingPost.from_group(g_message_id=g_message.message_id, admin_group_id=admin_group.id) is None

            await telegram.send_forward_message(
                forward_message=c_message,
                chat=channel_group,
                is_automatic_forward=True,
                user=TGUser(1, first_name="Telegram", is_bot=False),
            )
            assert telegram.last_message.text.startswith("by: ")
            if Config.post_get("comments"):
                assert PublishedPost.from_channel(channel_group.id, telegram.last_message.id) is not None
            else:
                assert PublishedPost.from_channel(channel.id, c_message.id) is not None

    class TestRejectSpot:
        """Tests the complete publishing spot pipeline"""

        async def test_reject_spot(
            self, telegram: TelegramSimulator, user: TGUser, admin_group: Chat, pending_post: Message
        ):
            """
            Complete with no the spot conversation
            """
            user2 = TGUser(2, first_name="Test2", is_bot=False)
            await telegram.send_callback_query(text="🔴 0", message=pending_post)
            await telegram.send_callback_query(text="🔴 1", message=telegram.last_message, user=user2)

            assert telegram.last_message.text.startswith("Il tuo ultimo post è stato rifiutato")
            assert telegram.messages[-2].reply_markup.inline_keyboard[0][1].text == f"🔴 @{user.id}"
            assert telegram.messages[-2].reply_markup.inline_keyboard[1][1].text == f"🔴 @{user2.id}"
            assert telegram.messages[-2].reply_markup.inline_keyboard[2][0].text == REJECTED_KB
            assert PendingPost.from_group(g_message_id=pending_post.message_id, admin_group_id=admin_group.id) is None

        async def test_reject_after_autoreply_spot(self, telegram: TelegramSimulator, pending_post: Message):
            """
            Test the reject spot after the autoreply
            """
            if not Config.settings_get("post", "reject_after_autoreply"):
                pytest.skip("Reject after autoreply is disabled")

            await telegram.send_callback_query(text="⏹ Stop", message=pending_post)
            autoreplies = Config.autoreplies_get("autoreplies")
            first_autoreply_key = list(autoreplies.keys())[0]
            await telegram.send_callback_query(
                text=first_autoreply_key, message=pending_post, data=f"autoreply,{first_autoreply_key}"
            )
            assert telegram.messages[-2].text == autoreplies[first_autoreply_key]
            assert telegram.last_message.text.startswith("Il tuo ultimo post è stato rifiutato")
            assert (
                telegram.messages[-3].reply_markup.inline_keyboard[-1][0].text
                == f"{REJECTED_KB} [{first_autoreply_key}]"
            )

    class TestStoppedSpot:
        """Tests the stopped spot and its navigation for autoreplies"""

        async def test_spot_stop(self, telegram: TelegramSimulator, pending_post: Message):
            """Tests the /spot command.
            Complete with yes the spot conversation
            """
            await telegram.send_callback_query(text="⏹ Stop", message=pending_post)
            assert telegram.last_message.reply_markup.inline_keyboard[-1][1].text == "▶️ Resume"

        @pytest.mark.parametrize("autoreply_key", list(Config.autoreplies_get("autoreplies").keys()))
        async def test_stop_spot(self, telegram: TelegramSimulator, pending_post: Message, autoreply_key: str):
            """
            Test autoreplies and navigation on the stopped spot
            """
            await self.test_spot_stop(telegram, pending_post)
            autoreply_message = Config.autoreplies_get("autoreplies")[autoreply_key]
            # find if the autoreply is in the keyboard
            autoreply_found = False
            next_button = telegram.find_button_on_keyboard("⏭ Next", telegram.last_message)

            while next_button:
                if telegram.find_button_on_keyboard(autoreply_key, telegram.last_message):
                    autoreply_found = True
                    break
                next_button = telegram.find_button_on_keyboard("⏭ Next", telegram.last_message)

                if next_button:
                    await telegram.send_callback_query(text="⏭ Next", message=telegram.last_message)

            assert autoreply_found is True

            await telegram.send_callback_query(
                text=autoreply_key, data=f"autoreply,{autoreply_key}", message=telegram.last_message
            )

            if Config.settings_get("post", "reject_after_autoreply"):
                assert telegram.messages[-2].text == autoreply_message
                assert telegram.last_message.text.startswith("Il tuo ultimo post è stato rifiutato")
                return

            assert telegram.last_message.text == autoreply_message

    class TestComments:
        """Tests the comments feature in the channel group"""

        async def test_non_anonymous_comment_msg(
            self, telegram: TelegramSimulator, published_post: Message, channel_group: Chat
        ):
            """Tests a public comment.
            The bot should not react to the message if the user is not anonymous
            """
            public_comment = await telegram.send_message(
                "Public comment",
                chat=channel_group,
                reply_to_message=published_post.reply_to_message,
                user=TGUser(10, first_name="user", is_bot=False),
            )

            assert telegram.get_message_by_id(public_comment.message_id) is not None
            assert telegram.last_message.text == "Public comment"
            assert telegram.last_message.from_user.is_bot is False

        async def test_anonymous_comment_msg(
            self, telegram: TelegramSimulator, published_post: Message, channel: Chat, channel_group: Chat
        ):
            """Tests the replacement of an anonymous comment.
            Copies the message and deletes the original
            """
            anonymous_comment = await telegram.send_message(
                "Anonymous comment",
                chat=channel_group,
                reply_to_message=published_post.reply_to_message,
                user=TGUser(10, first_name="user", is_bot=False),
                sender_chat=channel,
            )

            assert telegram.get_message_by_id(anonymous_comment.message_id) is None  # the anonymous comment is deleted
            assert telegram.last_message.text == "Anonymous comment"
            assert telegram.last_message.from_user.is_bot is True

    class TestFollow:
        """Tests the follow feature"""

        async def test_follow_callback(
            self, telegram: TelegramSimulator, published_post: Message, channel_group: Chat, user: TGUser
        ):
            """Tests the follow callback under the spot.
            The user shall be added to the followers of the post in the database
            """

            await telegram.send_callback_query(text="👁 Follow", message=published_post, user=user)

            assert telegram.last_message.text == "Stai seguendo questo spot"
            followed_message_id = (
                published_post.reply_to_message.message_id if Config.post_get("comments") else published_post.message_id
            )
            assert User(user.id).is_following(followed_message_id)

        async def test_unfollow_callback(
            self, telegram: TelegramSimulator, published_post: Message, channel_group: Chat, user: TGUser
        ):
            """Tests the follow callback under the spot.
            Since it was already following the spot, the user shall now be removed from the followers of the post
            """

            await self.test_follow_callback(telegram, published_post, channel_group, user)

            await telegram.send_callback_query(text="👁 Follow", message=published_post, user=user)

            assert telegram.last_message.text == "Non stai più seguendo questo spot"
            followed_message_id = (
                published_post.reply_to_message.message_id if Config.post_get("comments") else published_post.message_id
            )
            assert not User(user.id).is_following(followed_message_id)

        async def test_receive_follow_message(
            self, telegram: TelegramSimulator, published_post: Message, channel_group: Chat, user: TGUser
        ):
            """Tests the follow functionality.
            Since the user is following the spot, they shall receive a message when a new comment is posted
            """
            user2 = TGUser(2, first_name="User2", is_bot=False, username="user2")

            await self.test_follow_callback(telegram, published_post, channel_group, user)

            message_thread_id = (
                published_post.reply_to_message.message_id if Config.post_get("comments") else published_post.message_id
            )
            await telegram.send_message(
                "Test follow",
                chat=channel_group,
                user=user2,
                reply_to_message=message_thread_id,
                message_thread_id=message_thread_id,
            )
            assert telegram.last_message.text == "Test follow"
            assert telegram.last_message.from_user.is_bot is True
            assert telegram.last_message.chat_id == user.id

        async def test_skip_follow_message_same_user(
            self, telegram: TelegramSimulator, published_post: Message, channel_group: Chat, user: TGUser
        ):
            """Tests the follow functionality.
            Although the user is following the spot, they shall not receive a message when they post a comment
            """
            await self.test_follow_callback(telegram, published_post, channel_group, user)

            message_thread_id = (
                published_post.reply_to_message.message_id if Config.post_get("comments") else published_post.message_id
            )
            await telegram.send_message(
                "Test follow",
                chat=channel_group,
                user=user,
                reply_to_message=message_thread_id,
                message_thread_id=message_thread_id,
            )
            assert telegram.last_message.from_user.is_bot is False
            assert telegram.last_message.chat_id == channel_group.id  # The last message is stil the post
