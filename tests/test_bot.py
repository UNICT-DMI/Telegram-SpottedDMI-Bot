"""Tests the bot functionality"""

# This test isn't currently used, but it is ready if someone wants to actually implement this

# import pytest
# from telethon.sync import TelegramClient
# from telethon.tl.custom.message import Message
# from telethon.tl.custom.conversation import Conversation
# from modules.data.data_reader import config_map

# TIMEOUT = 8
# bot_tag = config_map['test']['bot_tag']

# class TestBot:

#     class TestMarkdownCommands:

#         @pytest.mark.asyncio
#         async def test_start_cmd(self, client: TelegramClient):
#             """Tests the start command

#             Args:
#                 client (TelegramClient): client used to simulate the user
#             """
#             async with client.conversation(bot_tag, timeout=TIMEOUT) as conv:
#                 await conv.send_message("/start")  # send a command
#                 resp: Message = await conv.get_response()
#                 assert resp.text

#         @pytest.mark.asyncio
#         async def test_help_cmd(self, client: TelegramClient):
#             """Tests the help command

#             Args:
#                 client (TelegramClient): client used to simulate the user
#             """
#             async with client.conversation(bot_tag, timeout=TIMEOUT) as conv:
#                 await conv.send_message("/help")  # send a command
#                 resp: Message = await conv.get_response()

#                 assert resp.text

#         @pytest.mark.asyncio
#         async def test_rules_cmd(self, client: TelegramClient):
#             """Tests the rules command

#             Args:
#                 client (TelegramClient): client used to simulate the user
#             """
#             async with client.conversation(bot_tag, timeout=TIMEOUT) as conv:
#                 await conv.send_message("/rules")  # send a command
#                 resp: Message = await conv.get_response()

#                 assert resp.text

#     class TestSpot:

#         async def user_spot(self, conv: Conversation) -> Message:
#             await conv.send_message("/cancel")  # send a command
#             await conv.get_response()

#             await conv.send_message("/spot")  # send a command
#             resp: Message = await conv.get_response()

#             assert resp.text

#             await conv.send_message("Testing spot")  # send a message
#             resp: Message = await conv.get_response()

#             assert resp.text

#             await resp.click(data="meme_confirm,yes")  # click inline keyboard
#             resp: Message = await conv.get_edit()

#             assert resp.text

#             resp: Message = await conv.get_response()
#             assert resp.text
#             return resp

#         @pytest.mark.asyncio
#         async def test_post_conversation_yes(self, client: TelegramClient):
#             """Tests the whole flow of the create conversation with the default image
#             The image creation is handled by the main thread

#             Args:
#                 client (TelegramClient): client used to simulate the user
#             """
#             async with client.conversation(bot_tag, timeout=TIMEOUT) as conv:
#                 await self.user_spot(conv)

#         @pytest.mark.asyncio
#         async def test_post_conversation_no(self, client: TelegramClient):
#             """Tests the whole flow of the create conversation with the default image
#             The image creation is handled by the main thread

#             Args:
#                 client (TelegramClient): client used to simulate the user
#             """
#             async with client.conversation(bot_tag, timeout=TIMEOUT) as conv:
#                 await conv.send_message("/cancel")  # send a command
#                 await conv.get_response()

#                 await conv.send_message("/spot")  # send a command
#                 resp: Message = await conv.get_response()

#                 assert resp.text

#                 await conv.send_message("Testing spot")  # send a message
#                 resp: Message = await conv.get_response()

#                 assert resp.text

#                 await resp.click(data="meme_confirm,no")  # click inline keyboard
#                 resp: Message = await conv.get_edit()

#                 assert resp.text

#         @pytest.mark.asyncio
#         async def test_settings_anonym(self, client: TelegramClient):
#             """Tests the whole flow of the create conversation with the default image
#             The image creation is handled by the main thread

#             Args:
#                 client (TelegramClient): client used to simulate the user
#             """
#             async with client.conversation(bot_tag, timeout=TIMEOUT) as conv:
#                 await conv.send_message("/settings")  # send a command
#                 resp: Message = await conv.get_response()

#                 assert resp.text

#                 await resp.click(data="meme_settings,anonimo")  # click inline keyboard
#                 resp: Message = await conv.get_edit()

#                 assert resp.text

#         @pytest.mark.asyncio
#         async def test_settings_credit(self, client: TelegramClient):
#             """Tests the whole flow of the create conversation with the default image
#             The image creation is handled by the main thread

#             Args:
#                 client (TelegramClient): client used to simulate the user
#             """
#             async with client.conversation(bot_tag, timeout=TIMEOUT) as conv:
#                 await conv.send_message("/settings")  # send a command
#                 resp: Message = await conv.get_response()

#                 assert resp.text

#                 await resp.click(data="meme_settings,credit")  # click inline keyboard
#                 resp: Message = await conv.get_edit()

#                 assert resp.text

#         @pytest.mark.asyncio
#         async def test_approve_yes(self, client: TelegramClient):
#             """Tests the whole flow of the create conversation with the default image
#             The image creation is handled by the main thread

#             Args:
#                 client (TelegramClient): client used to simulate the user
#             """
#             async with client.conversation(bot_tag, timeout=TIMEOUT) as conv:
#                 resp = await self.user_spot(conv)

#                 await resp.click(data="meme_approve_yes,")  # approve the spot
#                 resp: Message = await conv.get_edit()

#                 assert resp.reply_markup is None

#                 resp: Message = await conv.get_response()
#                 assert resp.reply_markup is not None

#         @pytest.mark.asyncio
#         async def test_approve_no(self, client: TelegramClient):
#             """Tests the whole flow of the create conversation with the default image
#             The image creation is handled by the main thread

#             Args:
#                 client (TelegramClient): client used to simulate the user
#             """
#             async with client.conversation(bot_tag, timeout=TIMEOUT) as conv:
#                 resp = await self.user_spot(conv)

#                 await resp.click(data="meme_approve_no,")  # approve the spot
#                 resp: Message = await conv.get_edit()

#                 assert resp.reply_markup is None

#         @pytest.mark.asyncio
#         async def test_reply_cmd(self, client: TelegramClient):
#             """Tests the whole flow of the create conversation with the default image
#             The image creation is handled by the main thread

#             Args:
#                 client (TelegramClient): client used to simulate the user
#             """
#             pass
