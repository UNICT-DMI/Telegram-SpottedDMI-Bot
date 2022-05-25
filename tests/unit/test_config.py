# pylint: disable=unused-argument,redefined-outer-name
"""Test all the modules related to data management"""
import os
import pytest
import yaml
from modules.data import Config

TEST_SETTINGS = {"string": "string", "int": 1, "bool": True, "meme": {"key": "value", "key2": 1}}
TEST_SETTINGS_TYPES = {"string": "string", "int": "int", "bool": "bool", "meme": {"key": "string", "key2": "int"}}


@pytest.fixture(scope="function")
def config() -> Config:
    """Called at the beginning of the testing session.
    Makes sure the config object is initialized

    Yields:
        Iterator[dict]: dictionary containing the results for the test queries
    """
    old_path = Config.SETTINGS_PATH
    Config.SETTINGS_PATH = ("tests", "settings.yaml")
    with open("tests/settings.yaml", 'w', encoding='utf-8') as settings:
        yaml.safe_dump(TEST_SETTINGS, settings)
    with open("tests/settings.yaml.types", 'w', encoding='utf-8') as settings:
        yaml.safe_dump(TEST_SETTINGS_TYPES, settings)
    Config.reset_settings()

    yield Config

    os.remove("tests/settings.yaml")
    os.remove("tests/settings.yaml.types")
    Config.SETTINGS_PATH = old_path
    Config.reset_settings()


class TestConfig:
    """Test the Config class"""

    def test_load_flat_settings(self, config: Config):
        """Tests the ability of the config object to load settings from a file"""

        for key, value in TEST_SETTINGS.items():
            assert config.settings_get(key) == value

    def test_load_nested_settings(self, config: Config):
        """Tests the ability of the config object to load settings from a file with nested properties"""

        for key, value in TEST_SETTINGS['meme'].items():
            assert config.settings_get("meme", key) == value

    def test_default_flat_settings(self, config: Config):
        """Tests the ability of the config object to return the default value
        if the key is not found
        """
        assert Config.settings_get("invalid_key") is None
        assert Config.settings_get("invalid_key", default="value") == "value"

    def test_default_nested_settings(self, config: Config):
        """Tests the ability of the config object to return the default value
        if the nested key is not found
        """
        assert Config.settings_get("invalid_key", "nested") is None
        assert Config.settings_get("invalid_key", "nested", default="value") == "value"

        assert Config.settings_get("string", "nested") is None
        assert Config.settings_get("string", "nested", default="value") == "value"

    def test_load_env_flat_settings(self, config: Config):
        """Tests the ability of the config object to load settings from the env vars"""

        os.environ["int"] = "2"
        os.environ["bool"] = "False"
        config.reset_settings()
        assert config.settings_get("int") == 2
        assert config.settings_get("bool") is False

    def test_load_env_nested_settings(self, config: Config):
        """Tests the ability of the config object to load settings from the env vars
        with the nested meme and test keys
        """
        os.environ["meme_key2"] = "2"
        os.environ["test_key"] = "test"
        config.reset_settings()
        assert config.settings_get("meme", "key2") == 2
        assert config.settings_get("test", "key") == "test"
