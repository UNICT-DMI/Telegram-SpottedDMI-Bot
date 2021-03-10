"""Test configuration"""
import asyncio
import warnings
import pytest
import yaml
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telegram.ext import Updater
from main import add_commands, add_handlers, add_jobs
from modules.data.db_manager import DbManager
from modules.data import config_map

api_id = config_map['test']['api_id']
api_hash = config_map['test']['api_hash']
session = config_map['test']['session']


def get_session():
    """Shows the String session.
    The string found must be inserted in the settings.yaml file
    """
    with TelegramClient(StringSession(), api_id, api_hash) as connection:
        print("Your session string is:", connection.session.save())


@pytest.fixture(scope="session")
def event_loop():
    """Allows to use @pytest.fixture(scope="session") for the folowing functions

    Yields:
        AbstractEventLoop: loop to be executed
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def bot_initialize():
    """Called at the beginning of the testing session.
    Modifies the configuration of the bot to make it suited for testing

    Yields:
        None: wait for the testing session to end
    """
    config_map['token'] = config_map['test']['token']
    config_map['meme']['n_votes'] = 1
    warnings.filterwarnings("ignore",
                            message="If 'per_message=False', 'CallbackQueryHandler' will not be tracked for every message.")
    yield None


@pytest.fixture(scope="session")
async def bot(bot_initialize):
    """Called at the beginning of the testing session.
    Starts the bot with the testing setting in another thread

    Yields:
        None: wait for the testing session to end
    """
    print("[info] started telegram bot")
    updater = Updater(config_map['token'], request_kwargs={'read_timeout': 20, 'connect_timeout': 20}, use_context=True)
    add_commands(updater)
    add_handlers(updater.dispatcher)
    add_jobs(updater.dispatcher)
    updater.start_polling()

    yield None

    updater.stop()
    print("[info] closed telegram bot")


@pytest.fixture(scope="session")
async def client(bot) -> TelegramClient:
    """Called at the beginning of the testing session.
    Creates the telegram client that will simulate the user

    Yields:
        Iterator[TelegramClient]: telegram client that will simulate the user
    """
    print("[info] started telegram client")
    tg_client = TelegramClient(StringSession(session), api_id, api_hash, sequential_updates=True)

    await tg_client.connect()  # Connect to the server
    await tg_client.get_me()  # Issue a high level command to start receiving message
    await tg_client.get_dialogs()  # Fill the entity cache

    yield tg_client

    await tg_client.disconnect()
    await tg_client.disconnected

    print("[info] closed telegram client")


@pytest.fixture(scope="session")
async def db_results() -> dict:
    """Called at the beginning of the testing session.
    Creates initializes the database

    Yields:
        Iterator[dict]: dictionary containing the results for the test queries
    """
    print("[info] initialized the db")

    DbManager.query_from_file("data/db/db_test.sql")

    with open("tests/db_results.yaml", 'r') as yaml_config:
        results = yaml.load(yaml_config, Loader=yaml.SafeLoader)

    yield results

    DbManager.query_from_string("DROP TABLE IF EXISTS test_table;")

    print("[info] closed db")


if __name__ == "__main__":
    get_session()
