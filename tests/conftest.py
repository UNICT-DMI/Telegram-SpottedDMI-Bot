# pylint: disable=redefined-outer-name
"""Test configuration"""
import os

import pytest

from spotted.data import Config, DbManager


@pytest.fixture(scope="class", autouse=True)
def setup():
    """Called at the beginning of the testing session.
    Sets up the test configuration
    """
    Config.SETTINGS_PATH = ""  # ensure that no user config are loaded
    Config.AUTOREPLIES_PATH = ""  # ensure that no user autoreplies are loaded
    Config.reload(True)
    Config.override_settings(
        {
            "token": "1234567890:qY9gv7pRJgFj4EVmN3Z1gfJOgQpCbh0vmp5",
            "bot_tag": "@test_bot",
            "debug": {
                "db_file": "test_db.sqlite3",
            },
        }
    )


@pytest.fixture(scope="session")
def create_test_db() -> DbManager:
    """Called once per at the beginning of this class.
    Creates and initializes the local database
    """
    yield DbManager
    os.remove(Config.debug_get("db_file"))


@pytest.fixture(scope="function")
def test_table(create_test_db: DbManager) -> DbManager:
    """Called once per at the beginning of each function.
    Resets the state of the database
    """
    create_test_db.query_from_file("config", "db", "post_db_del.sql")
    create_test_db.query_from_file("config", "db", "post_db_init.sql")
    return create_test_db
