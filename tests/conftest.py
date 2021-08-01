"""Test configuration"""
import warnings
import pytest
from modules.data import config_map


@pytest.fixture(scope="session", autouse=True)
def setup():
    """Called at the beginning of the testing session.
    Sets up the test configuration
    """
    # Disable the Conversation handler warnings
    warnings.filterwarnings("ignore",
                            message="If 'per_message=False', 'CallbackQueryHandler' will not be tracked for every message.")

    for test_key in config_map['test']:
        if test_key in config_map:
            config_map[test_key] = config_map['test'][test_key]
        if test_key in config_map['meme']:
            config_map['meme'][test_key] = config_map['test'][test_key]
