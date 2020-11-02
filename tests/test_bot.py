"""Tests the bot functionality"""

# This test isn't currently used, but it is ready if someone wants to actually implement this

# import time
# import re
# import pytest
# from telethon.sync import TelegramClient
# from telethon.tl.custom.message import Message
# from telethon.tl.custom.conversation import Conversation
# from modules.data.data_reader import config_map, read_md

# TIMEOUT = 8
# bot_tag = config_map['test']['tag']


# def teardown():
#     """Makes so that there is a fixed timeout between each test
#     """
#     time.sleep(1)


# def get_telegram_md(message_text: str) -> str:
#     """Gets the message received from the bot and reverts it to the Markdowm_v2 used to send messages with it

#     Args:
#         message_text (str): text of the message received from the bot

#     Returns:
#         str: the same text of the message, but with the Markdown_v2 conventions
#     """
#     message_text = re.sub(r"(?<=[^_])_(?=[^_])", r"\_", message_text)  # _ -> \_
#     message_text = re.sub(r"\.(?![^(]*\))", r"\.", message_text)  # . -> \.
#     message_text = re.sub(r"-(?![^(]*\))", r"\-", message_text)  # . -> \.
#     return message_text.replace("__", "_").replace("**", "*").replace("!", "\\!")


# @pytest.mark.asyncio
# async def test_start_cmd(client: TelegramClient):
#     """Tests the start command

#     Args:
#         client (TelegramClient): client used to simulate the user
#     """
#     conv: Conversation
#     async with client.conversation(bot_tag, timeout=TIMEOUT) as conv:
#         await conv.send_message("/start")  # send a command
#         resp: Message = await conv.get_response()

#         assert read_md("start") == get_telegram_md(resp.text)


# @pytest.mark.asyncio
# async def test_help_cmd(client: TelegramClient):
#     """Tests the help command

#     Args:
#         client (TelegramClient): client used to simulate the user
#     """
#     conv: Conversation
#     async with client.conversation(bot_tag, timeout=TIMEOUT) as conv:
#         await conv.send_message("/help")  # send a command
#         resp: Message = await conv.get_response()

#         assert read_md("help") == get_telegram_md(resp.text)


# @pytest.mark.asyncio
# async def test_rules_cmd(client: TelegramClient):
#     """Tests the rules command

#     Args:
#         client (TelegramClient): client used to simulate the user
#     """
#     conv: Conversation
#     async with client.conversation(bot_tag, timeout=TIMEOUT) as conv:
#         await conv.send_message("/rules")  # send a command
#         resp: Message = await conv.get_response()

#         assert read_md("rules") == get_telegram_md(resp.text)


# @pytest.mark.asyncio
# async def test_post_conversation(client: TelegramClient):
#     """Tests the whole flow of the create conversation with the default image
#     The image creation is handled by the main thread

#     Args:
#         client (TelegramClient): client used to simulate the user
#     """
#     conv: Conversation
#     async with client.conversation(bot_tag, timeout=TIMEOUT) as conv:
#         await conv.send_message("/post")  # send a command
#         resp: Message = await conv.get_response()

#         assert get_telegram_md(resp.text) == "Invia il post che vuoi pubblicare"

#         await conv.send_message("Testing")  # click inline keyboard
#         resp: Message = await conv.get_response()

#         assert get_telegram_md(resp.text) == "Sei sicuro di voler publicare questo post?"

#         await resp.click(text="No")  # send a message
#         resp: Message = await conv.get_edit()

#         assert get_telegram_md(resp.text) == "Va bene, alla prossima 🙃"
