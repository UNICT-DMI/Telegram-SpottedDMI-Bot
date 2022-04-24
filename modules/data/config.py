"""Read the bot configuration from the settings.yaml and the reactions.yaml files"""
import os
import re
from typing import Any, Iterable, Literal
import yaml

SettingsKeys = Literal["debug", "meme", "test", "token", "bot_tag"]
SettingsDebugKeys = Literal["local_log", "reset_on_load"]
SettingsMemeKeys = Literal["channel_group_id", "channel_id", "channel_tag", "comments", "group_id", "n_votes",
                           "remove_after_h", "tag", "report", "report_wait_mins", "replace_anonymous_comments",
                           "delete_anonymous_comments",]
SettingsTestKeys = Literal[Literal["api_hash", "api_id", "session", "bot_tag", "token"], SettingsMemeKeys]
SettingsKeysType = Literal[SettingsKeys, SettingsMemeKeys, SettingsDebugKeys, SettingsTestKeys]

ReactionKeysType = Literal["reactions", "rows"]


class Config():
    """Configurations"""
    SETTINGS_PATH = ("config", "settings.yaml")
    REACTION_PATH = ("data", "yaml", "reactions.yaml")
    __instance: 'Config' = None

    @classmethod
    def reset_settings(cls):
        """Reset the configuration"""
        cls.__instance = None

    @staticmethod
    def __get(config: dict, *keys: str, default: Any = None) -> Any:
        """Get the value of the specified key in the configuration.
        If the key is a tuple, it will return the value of the nested key.
        If the key is not present, it will return the default value.

        Args:
            config (dict): configuration dict to search
            key (str): key to search
            default (Any, optional): default value to return if the key is not present. Defaults to None.

        Returns:
            Any: value of the key or default value
        """
        for k in keys:
            if isinstance(config, Iterable) and k in config:
                config = config[k]
            else:
                return default
        return config

    @classmethod
    def __get_instance(cls) -> 'Config':
        """Singleton getter

        Returns:
            Config: instance of the Config class
        """
        if cls.__instance is None:
            cls()
        return cls.__instance

    @classmethod
    def meme_get(cls, key: SettingsMemeKeys, default: Any = None) -> Any:
        """Get the value of the specified key in the configuration under the 'meme' section.
        If the key is not present, it will return the default value.

        Args:
            key (SettingsMemeKeys): key to get
            default (Any, optional): default value to return if the key is not present. Defaults to None.

        Returns:
            Any: value of the key or default value
        """
        return cls.settings_get("meme", key, default=default)

    @classmethod
    def settings_get(cls, *keys: SettingsKeysType, default: Any = None) -> Any:
        """Get the value of the specified key in the configuration.
        If the key is a tuple, it will return the value of the nested key.
        If the key is not present, it will return the default value.

        Args:
            key (SettingsKeyType): key to get
            default (Any, optional): default value to return if the key is not present. Defaults to None.

        Returns:
            Any: value of the key or default value
        """
        instance = cls.__get_instance()
        return cls.__get(instance.settings, *keys, default=default)

    @classmethod
    def reactions_get(cls, *keys: ReactionKeysType, default: Any = None) -> Any:
        """Get the value of the specified key in the reactions configuration dictionary.
        If the key is a tuple, it will return the value of the nested key.
        If the key is not present, it will return the default value.

        Args:
            key (ReactionKeyType): key to get
            default (Any, optional): default value to return if the key is not present. Defaults to None.

        Returns:
            Any: value of the key or default value
        """
        instance = cls.__get_instance()
        return cls.__get(instance.reactions, *keys, default=default)

    @classmethod
    def override_test_settings(cls):
        """Overrides the settings with the test settings"""
        instance = cls.__get_instance()
        for test_key in cls.settings_get("test"):
            if test_key in instance.settings:
                instance.settings[test_key] = cls.settings_get("test", test_key)
            if test_key in instance.settings["meme"]:
                instance.settings['meme'][test_key] = cls.settings_get("test", test_key)

    def __init__(self):
        if Config.__instance is not None:
            raise Exception("This class is a singleton!")

        Config.__instance = self
        root_path = os.path.join(os.path.dirname(__file__), "..", "..")
        self.settings_path = os.path.join(root_path, *self.SETTINGS_PATH)
        self.reaction_path = os.path.join(root_path, *self.REACTION_PATH)

        # Read the local configuration.
        # First, load the .default file, than override it with any non .default file
        self.settings = self.__load_configuration(self.settings_path, force_load=True)
        self.reactions = self.__load_configuration(self.reaction_path)

        # Read the environment configuration, if present, and override the settings
        self.__read_env_settings()
        self.__validate_types_settings()

    @classmethod
    def __merge_settings(cls, d: dict, u: dict) -> dict:
        """Merges two configuration dictionaries.

        Args:
            d (dict): dict to merge. It will be modified
            u (dict): dict to merge with

        Returns:
            dict: merged dictionaries
        """
        for k, v in u.items():
            if isinstance(v, dict):
                d[k] = cls.__merge_settings(d.get(k, {}), v)
            else:
                d[k] = v
        return d

    @classmethod
    def __load_configuration(cls, path: str, load_default: bool = True, force_load: bool = False) -> dict:
        """Loads the configuration from the .yaml file specified in the path and stores it as a dict.
        If load_default is True, it will first look for any file with the same name and the .default extension.
        Then the values will be overwritten by the specified file, if present.
        If force_load is True, the program will crash if the specified file is not present

        Args:
            path (str): path of the configuration .yaml file
            load_default (bool, optional): whether to look for the .default file first for the default configuration. Defaults to True.
            force_load (bool, optional): whether to force the presence of the specified file. Defaults to False.

        Returns:
            dict: configuration dictionary
        """
        conf = {}
        if load_default and os.path.exists(f"{path}.default"):
            with open(f"{path}.default", 'r', encoding="utf-8") as conf_file:
                conf = cls.__merge_settings(conf, yaml.load(conf_file, Loader=yaml.SafeLoader))
        if force_load or os.path.exists(path):
            with open(path, 'r', encoding="utf-8") as conf_file:
                conf = cls.__merge_settings(conf, yaml.load(conf_file, Loader=yaml.SafeLoader))
        return conf

    def __read_env_settings(self):
        """Reads the enviroment variables and stores the values in the config dict.
        Any key already present will be overwritten
        """
        new_vars = {}
        self.settings['test'] = self.settings['test'] if self.settings.get('test', False) else {}
        self.settings['meme'] = self.settings['meme'] if self.settings.get('meme', False) else {}
        env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
        if os.path.exists(env_path):
            envre = re.compile(r'''^([^\s=]+)=(?:[\s"']*)(.+?)(?:[\s"']*)$''')
            with open(env_path, "r", encoding="utf-8") as env:
                for line in env:
                    match = envre.match(line)
                    if match is not None:
                        new_vars[match.group(1).lower()] = match.group(2)

        for key in os.environ:
            new_vars[key.lower()] = os.getenv(key)

        for key, value in new_vars.items():
            if key.startswith("test_"):
                self.settings['test'][key[5:]] = value
            elif key.startswith("meme_"):
                self.settings['meme'][key[5:]] = value
            else:
                self.settings[key] = value

    def __validate_types_settings(self):
        """Validates the settings values in the 'meme' section, casting them when necessary
        """
        if not os.path.exists(f"{self.settings_path}.types"):
            return
        with open(f"{self.settings_path}.types", 'r', encoding="utf-8") as conf_file:
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
                    elif types[key] == "array":
                        if isinstance(conf[key], str):
                            conf[key] = conf[key].split(",")
                    else:
                        conf[key] = str(conf[key])
