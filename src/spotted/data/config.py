"""Read the bot configuration from the settings.yaml and the autoreplies.yaml files"""
import logging
import os
import re
from importlib import resources
from typing import Any, Iterable, Literal

import yaml

SettingsKeys = Literal["debug", "post", "test", "token", "bot_tag"]
SettingsDebugKeys = Literal["local_log", "reset_on_load", "log_file", "log_error_file", "db_file"]
SettingsPostKeys = Literal[
    "community_group_id",
    "channel_id",
    "channel_tag",
    "comments",
    "admin_group_id",
    "n_votes",
    "remove_after_h",
    "report",
    "report_wait_mins",
    "replace_anonymous_comments",
    "delete_anonymous_comments",
]
SettingsKeysType = Literal[SettingsKeys, SettingsPostKeys, SettingsDebugKeys]
AutorepliesKeysType = Literal["autoreplies"]

logger = logging.getLogger(__name__)


class Config:
    """Configurations"""

    DEFAULT_SETTINGS_PATH = os.path.join(resources.files("spotted"), "config", "yaml", "settings.yaml")
    DEFAULT_AUTOREPLIES_PATH = os.path.join(resources.files("spotted"), "config", "yaml", "autoreplies.yaml")
    __instance: "Config | None" = None

    SETTINGS_PATH = "settings.yaml"
    AUTOREPLIES_PATH = "autoreplies.yaml"

    @classmethod
    def reload(cls, force_reload: bool = False):
        """Reset the configuration.
        The next time a setting parameter is required, the whole configuration will be reloaded.
        If force_reload is True, the configuration will be reloaded immediately.

        Args:
            force_reload: if True, the configuration will be reloaded immediately
        """
        cls.__instance = None
        if force_reload:
            cls.__get_instance()

    @staticmethod
    def __get(config: dict, *keys: str, default: Any = None) -> Any:
        """Get the value of the specified key in the configuration.
        If the key is a tuple, it will return the value of the nested key.
        If the key is not present, it will return the default value.

        Args:
            config: configuration dict to search
            key: key to search
            default: default value to return if the key is not present

        Returns:
            value of the key or default value
        """
        for k in keys:
            if isinstance(config, Iterable) and k in config:
                config = config[k]
            else:
                return default
        return config

    @classmethod
    def __get_instance(cls) -> "Config":
        """Singleton getter

        Returns:
            instance of the Config class
        """
        if cls.__instance is None:
            cls.__instance = cls()
        return cls.__instance

    @classmethod
    def post_get(cls, key: SettingsPostKeys, default: Any = None) -> Any:
        """Get the value of the specified key in the configuration under the 'post' section.
        If the key is not present, it will return the default value.

        Args:
            key: key to get
            default: default value to return if the key is not present

        Returns:
            value of the key or default value
        """
        return cls.settings_get("post", key, default=default)

    @classmethod
    def debug_get(cls, key: SettingsDebugKeys, default: Any = None) -> Any:
        """Get the value of the specified key in the configuration under the 'debug' section.
        If the key is not present, it will return the default value.

        Args:
            key: key to get
            default: default value to return if the key is not present

        Returns:
            value of the key or default value
        """
        return cls.settings_get("debug", key, default=default)

    @classmethod
    def settings_get(cls, *keys: SettingsKeysType, default: Any = None) -> Any:
        """Get the value of the specified key in the configuration.
        If the key is a tuple, it will return the value of the nested key.
        If the key is not present, it will return the default value.

        Args:
            key: key to get
            default: default value to return if the key is not present

        Returns:
            value of the key or default value
        """
        instance = cls.__get_instance()
        return cls.__get(instance.settings, *keys, default=default)

    @classmethod
    def autoreplies_get(cls, *keys: AutorepliesKeysType, default: Any = None) -> dict:
        """Get the value of the specified key in the autoreplies configuration dictionary.
        If the key is a tuple, it will return the value of the nested key.
        If the key is not present, it will return the default value.

        Args:
            key: key to get
            default: default value to return if the key is not present

        Returns:
            value of the key or default value
        """
        instance = cls.__get_instance()
        return cls.__get(instance.autoreplies, *keys, default=default)

    @classmethod
    def override_settings(cls, config: dict):
        """Overrides the settings with the configuration provided in the config dict.

        Args:
            config: configuration dict used to override the current settings
        """
        instance = cls.__get_instance()
        cls.__merge_settings(instance.settings, config)

    def __init__(self):
        if type(self).__instance is not None:
            raise RuntimeError("This class is a singleton!")

        # First, load the default configuration provided from the package
        self.settings = self.__load_configuration(self.DEFAULT_SETTINGS_PATH)
        self.autoreplies = self.__load_configuration(self.DEFAULT_AUTOREPLIES_PATH)

        # Then update the current configuration by loading the one provided by the user, if present
        # At least the settings file must exists, since we need to know the token
        self.__merge_settings(self.settings, self.__load_configuration(self.SETTINGS_PATH))
        self.__merge_settings(self.autoreplies, self.__load_configuration(self.AUTOREPLIES_PATH))

        # Read the environment configuration, if present, and override the settings
        self.__read_env_settings()
        # Validate the types of the settings
        self.__validate_types_settings()

        self.__log_errors_loaded_config()

    @classmethod
    def __merge_settings(cls, base: dict, update: dict) -> dict:
        """Merges two configuration dictionaries.

        Args:
            base: dict to merge. It will be modified
            update: dict to merge with

        Returns:
            merged dictionaries
        """
        for key, value in update.items():
            if isinstance(value, dict):
                base[key] = cls.__merge_settings(base.get(key, {}), value)
            else:
                base[key] = value
        return base

    @classmethod
    def __load_configuration(cls, path: str) -> dict:
        """Loads the configuration from the .yaml file specified in the path and stores it as a dict.
        If load_default is True, it will first look for any file with the same name and the .default extension.
        Then the values will be overwritten by the specified file, if present.
        If force_load is True, the program will crash if the specified file is not present

        Args:
            path: path of the configuration .yaml file

        Returns:
            configuration dictionary
        """
        conf = {}
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as conf_file:
                conf = cls.__merge_settings(conf, yaml.load(conf_file, Loader=yaml.SafeLoader))
        return conf

    def __read_env_settings(self):
        """Reads the environment variables and stores the values in the config dict.
        Any key already present will be overwritten
        """
        new_vars: dict[str, str] = {}
        self.settings["post"] = self.settings.get("post", {})
        self.settings["debug"] = self.settings.get("debug", {})
        env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
        if os.path.exists(env_path):
            env_re = re.compile(r"""^([^\s=]+)=(?:[\s"']*)(.+?)(?:[\s"']*)$""")
            with open(env_path, "r", encoding="utf-8") as env:
                for line in env:
                    match = env_re.match(line)
                    if match is not None:
                        new_vars[match.group(1).lower()] = match.group(2)

        for key in os.environ:
            new_vars[key.lower()] = os.getenv(key)

        for key, value in new_vars.items():
            if key.startswith("post_"):
                self.settings["post"][key[5:]] = value
            elif key.startswith("debug_"):
                self.settings["debug"][key[6:]] = value
            else:
                self.settings[key] = value

    def __validate_types_settings(self):
        """Validates the settings values in the 'post' section, casting them when necessary"""
        type_path = f"{self.DEFAULT_SETTINGS_PATH}.types"
        if not os.path.exists(type_path):
            return
        with open(type_path, "r", encoding="utf-8") as conf_file:
            types = yaml.load(conf_file, Loader=yaml.SafeLoader)
            self.__apply_type_validation(types, self.settings)

    def __apply_type_validation(self, types: dict, conf: dict):
        for key in types:
            if isinstance(types[key], dict):
                self.__apply_type_validation(types[key], conf[key])
            else:
                if key in conf:
                    if types[key] == "bool":
                        if isinstance(conf[key], str):
                            conf[key] = conf[key].lower() not in ("false", "0", "no", "")
                        else:
                            conf[key] = bool(conf[key])
                    elif types[key] == "int":
                        conf[key] = int(conf[key])
                    elif types[key] == "float":
                        conf[key] = float(conf[key])
                    elif types[key] == "list":
                        if isinstance(conf[key], str):
                            conf[key] = conf[key].split(",")
                    else:
                        conf[key] = str(conf[key])

    def __log_errors_loaded_config(self):
        """Evaluate the loaded configuration and log
        any anomaly or possible unintended configuration
        """
        logger.debug("Loaded settings")
        if self.settings.get("debug", {}).get("local_log", False):
            logger.debug("Local log enabled")
        if self.settings.get("debug", {}).get("reset_on_load", False):
            logger.warning("Reset on load enabled")
        if self.settings.get("token", "") == "":
            logger.error("Missing bot token")

    def __repr__(self):
        return f"Config({self.settings!r}, {self.autoreplies!r})"
