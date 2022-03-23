# pylint: disable=unused-argument,redefined-outer-name
"""Test all the modules related to data management"""
import os
import pytest
import yaml
from modules.data import DbManager, Config

TEST_SETTINGS = {"string": "string", "int": 1, "bool": True}
TEST_SETTINGS_TYPES = {"string": "string", "int": "int", "bool": "bool"}


@pytest.fixture(scope="function")
def config() -> Config:
    """Called at the beginning of the testing session.
    Makes sure the config object is initialized

    Yields:
        Iterator[dict]: dictionary containing the results for the test queries
    """
    old_path = Config.SETTINGS_PATH
    Config.SETTINGS_PATH = ("tests", "settings.yaml")
    with open("tests/settings.yaml", 'w') as settings:
        yaml.safe_dump(TEST_SETTINGS, settings)
    with open("tests/settings.yaml.types", 'w') as settings:
        yaml.safe_dump(TEST_SETTINGS_TYPES, settings)
    Config.reset_settings()

    yield Config

    os.remove("tests/settings.yaml")
    os.remove("tests/settings.yaml.types")
    Config.SETTINGS_PATH = old_path
    Config.reset_settings()


class TestConfig:

    def test_load_settings(self, config: Config):
        """Tests the ability of the config object to load settings from a file
        """
        for key in TEST_SETTINGS:
            assert config.settings_get(key) == TEST_SETTINGS[key]

    def test_load_env_settings(self, config: Config):
        """Tests the ability of the config object to load settings from the env vars
        """
        os.environ["int"] = "2"
        os.environ["bool"] = "False"
        config.reset_settings()
        assert config.settings_get("string") == "string"
        assert config.settings_get("int") == 2
        assert config.settings_get("bool") is False
