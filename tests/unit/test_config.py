# pylint: disable=unused-argument,redefined-outer-name
"""Test all the modules related to data management"""
import os
import pytest
import yaml
from modules.data import Config

TEST_SETTINGS = {
    "string": "string",
    "int": 1,
    "float": 2.3,
    "bool": True,
    "list": ["a", "b", "c", "d"],
    "meme": {
        "key": "value",
        "key2": 1
    },
    "debug": {
        "logs": ["value1", "value2"],
        "key2": 1
    }
}
TEST_SETTINGS_TYPES = {
    "string": "string",
    "int": "int",
    "float": "float",
    "bool": "bool",
    "list": "list",
    "meme": {
        "key": "string",
        "key2": "int"
    },
    "debug": {
        "logs": "list",
        "key2": "int"
    }
}


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

    def test_load_env_flat_settings_new_setting(self, config: Config):
        """Tests the ability of the config object to load a new setting from the env vars, 
        not present in the settings file.
        Only string values can be loaded this way
        """
        os.environ["new_setting"] = "new value"
        config.reset_settings()
        assert config.settings_get("new_setting") == "new value"
        del os.environ["new_setting"]

    def test_load_env_flat_settings_int(self, config: Config):
        """Tests the ability of the config object to load int settings from the env vars"""
        os.environ["int"] = "2"
        config.reset_settings()
        assert config.settings_get("int") == 2
        del os.environ["int"]

    def test_load_env_flat_settings_float(self, config: Config):
        """Tests the ability of the config object to load float settings from the env vars"""
        os.environ["float"] = "3.4"
        config.reset_settings()
        assert config.settings_get("float") == 3.4
        del os.environ["float"]

    def test_load_env_flat_settings_bool(self, config: Config):
        """Tests the ability of the config object to load bool settings from the env vars"""
        os.environ["bool"] = "False"
        config.reset_settings()
        assert config.settings_get("bool") is False
        del os.environ["bool"]

    def test_load_env_flat_settings_list(self, config: Config):
        """Tests the ability of the config object to load list settings from the env vars"""
        os.environ["list"] = "e,f,g"
        config.reset_settings()
        assert config.settings_get("list") == ["e", "f", "g"]
        del os.environ["list"]

    def test_load_env_flat_settings_str(self, config: Config):
        """Tests the ability of the config object to load str settings from the env vars"""
        os.environ["string"] = "another string"
        config.reset_settings()
        assert config.settings_get("string") == "another string"
        del os.environ["string"]

    def test_load_env_nested_meme_settings(self, config: Config):
        """Tests the ability of the config object to load settings from the env vars
        with the nested meme key
        """
        os.environ["meme_key2"] = "2"
        config.reset_settings()
        assert config.settings_get("meme", "key2") == 2
        del os.environ["meme_key2"]

    def test_load_env_nested_debug_settings(self, config: Config):
        """Tests the ability of the config object to load settings from the env vars
        with the nested debug key
        """
        os.environ["debug_logs"] = "val1,val2,val3"
        config.reset_settings()
        assert config.settings_get("debug", "logs") == ["val1", "val2", "val3"]
        del os.environ["debug_logs"]

    def test_load_env_nested_test_settings(self, config: Config):
        """Tests the ability of the config object to load settings from the env vars
        with the nested test key
        """
        os.environ["test_key"] = "test"
        config.reset_settings()
        assert config.settings_get("test", "key") == "test"
        del os.environ["test_key"]
