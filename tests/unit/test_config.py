# pylint: disable=unused-argument,redefined-outer-name
"""Test all the modules related to data management"""
import os

import pytest
import yaml

from spotted.data import Config

TEST_SETTINGS = {
    "string": "string",
    "int": 1,
    "float": 2.3,
    "bool": True,
    "list": ["a", "b", "c", "d"],
    "post": {"key": "value", "key2": 1},
    "debug": {"logs": ["value1", "value2"], "key2": 1},
}
TEST_SETTINGS_TYPES = {
    "string": "string",
    "int": "int",
    "float": "float",
    "bool": "bool",
    "list": "list",
    "post": {"key": "string", "key2": "int"},
    "debug": {"logs": "list", "key2": "int"},
}


@pytest.fixture(scope="function")
def config() -> Config:
    """Called at the beginning of the testing session.
    Makes sure the config object is initialized

    Yields:
        Iterator[dict]: dictionary containing the results for the test queries
    """
    old_default_path = Config.DEFAULT_SETTINGS_PATH

    Config.DEFAULT_SETTINGS_PATH = os.path.join("tests", "settings.yaml")  # set the test config path
    # create some custom default settings.yaml files
    with open(Config.DEFAULT_SETTINGS_PATH, "w", encoding="utf-8") as settings:
        yaml.safe_dump(TEST_SETTINGS, settings)
    with open(f"{Config.DEFAULT_SETTINGS_PATH}.types", "w", encoding="utf-8") as settings:
        yaml.safe_dump(TEST_SETTINGS_TYPES, settings)
    Config.reload()

    yield Config

    # remove the custom default settings.yaml files
    os.remove(Config.DEFAULT_SETTINGS_PATH)
    os.remove(f"{Config.DEFAULT_SETTINGS_PATH}.types")
    # restore the old settings
    Config.DEFAULT_SETTINGS_PATH = old_default_path


class TestConfig:
    """Test the Config class"""

    def assert_config(self, config: Config, base_key: str = None, exclude_keys: tuple = ()):
        """Tests the ability of the config object to load settings from a file"""
        settings_to_test = (
            TEST_SETTINGS if base_key is None or base_key not in TEST_SETTINGS else TEST_SETTINGS[base_key]
        )
        for key, value in settings_to_test.items():
            if key not in exclude_keys:
                if base_key is None:
                    assert config.settings_get(key) == value
                else:
                    assert config.settings_get(base_key, key) == value

    def test_load_flat_settings(self, config: Config):
        """Tests the ability of the config object to load settings from a file"""
        for key, value in TEST_SETTINGS.items():
            assert config.settings_get(key) == value

    def test_load_nested_settings(self, config: Config):
        """Tests the ability of the config object to load settings from a file with nested properties"""
        for key, value in TEST_SETTINGS["post"].items():
            assert config.settings_get("post", key) == value

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
        config.reload()
        assert config.settings_get("new_setting") == "new value"
        self.assert_config(config)  # Other settings are unchanged
        del os.environ["new_setting"]

    def test_load_env_flat_settings_int(self, config: Config):
        """Tests the ability of the config object to load int settings from the env vars"""
        os.environ["int"] = "2"
        config.reload()
        assert config.settings_get("int") == 2
        self.assert_config(config, exclude_keys=("int",))  # Other settings are unchanged
        del os.environ["int"]

    def test_load_env_flat_settings_float(self, config: Config):
        """Tests the ability of the config object to load float settings from the env vars"""
        os.environ["float"] = "3.4"
        config.reload()
        assert config.settings_get("float") == 3.4
        self.assert_config(config, exclude_keys=("float",))  # Other settings are unchanged
        del os.environ["float"]

    def test_load_env_flat_settings_bool(self, config: Config):
        """Tests the ability of the config object to load bool settings from the env vars"""
        os.environ["bool"] = "False"
        config.reload()
        assert config.settings_get("bool") is False
        self.assert_config(config, exclude_keys=("bool",))  # Other settings are unchanged
        del os.environ["bool"]

    def test_load_env_flat_settings_list(self, config: Config):
        """Tests the ability of the config object to load list settings from the env vars"""
        os.environ["list"] = "e,f,g"
        config.reload()
        assert config.settings_get("list") == ["e", "f", "g"]
        self.assert_config(config, exclude_keys=("list",))  # Other settings are unchanged
        del os.environ["list"]

    def test_load_env_flat_settings_str(self, config: Config):
        """Tests the ability of the config object to load str settings from the env vars"""
        os.environ["string"] = "another string"
        config.reload()
        assert config.settings_get("string") == "another string"
        self.assert_config(config, exclude_keys=("string",))  # Other settings are unchanged
        del os.environ["string"]

    def test_load_env_nested_post_settings(self, config: Config):
        """Tests the ability of the config object to load settings from the env vars
        with the nested post key
        """
        os.environ["post_key2"] = "2"
        config.reload()
        assert config.settings_get("post", "key2") == 2
        self.assert_config(config, exclude_keys=("post",))  # Other settings are unchanged
        self.assert_config(config, base_key="post", exclude_keys=("key2"))  # Other settings in post are unchanged
        del os.environ["post_key2"]

    def test_load_env_nested_debug_settings(self, config: Config):
        """Tests the ability of the config object to load settings from the env vars
        with the nested debug key
        """
        os.environ["debug_logs"] = "val1,val2,val3"
        config.reload()
        assert config.settings_get("debug", "logs") == ["val1", "val2", "val3"]
        self.assert_config(config, exclude_keys=("debug",))  # Other settings are unchanged
        self.assert_config(config, base_key="debug", exclude_keys=("logs",))  # Other settings in post are unchanged
        del os.environ["debug_logs"]
