"""Test configuration"""
import os
import warnings
import pytest
from modules.data import config_map, get_abs_path, DbManager


@pytest.fixture(scope="session", autouse=True)
def setup():
    """Called at the beginning of the testing session.
    Sets up the test configuration
    """
    # Disable the Conversation handler warnings
    warnings.filterwarnings("ignore", category=UserWarning)

    for test_key in config_map['test']:
        if test_key in config_map:
            config_map[test_key] = config_map['test'][test_key]
        if test_key in config_map['meme']:
            config_map['meme'][test_key] = config_map['test'][test_key]


@pytest.fixture(scope="session")
def init_local_test_db() -> DbManager:
    """Called once per at the beginning of this class.
    Creates and initializes the local database
    """
    DbManager.db_path = ('data', 'db', 'test_db.sqlite3')
    yield DbManager
    os.remove(get_abs_path('data', 'db', 'test_db.sqlite3'))
