"""Test configuration"""
import os
import warnings
import pytest
from modules.data import Config, get_abs_path, DbManager


@pytest.fixture(scope="session", autouse=True)
def setup():
    """Called at the beginning of the testing session.
    Sets up the test configuration
    """
    # Disable the Conversation handler warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    Config.override_test_settings()


@pytest.fixture(scope="session")
def init_local_test_db() -> DbManager:
    """Called once per at the beginning of this class.
    Creates and initializes the local database
    """
    DbManager.db_path = ('data', 'db', 'test_db.sqlite3')
    yield DbManager
    os.remove(get_abs_path('data', 'db', 'test_db.sqlite3'))
