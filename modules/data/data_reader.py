"""Read data from files"""
import os
import yaml
import re
from telegram.utils.helpers import escape_markdown


def get_abs_path(*root_file_path: str) -> str:
    r"""Get the abs path from the root directory of the project to the requested path

    Args:
        root_file_path (\*str): path from the root project directory

    Returns:
        str: corrisponding abs path
    """
    root_path = os.path.join(os.path.dirname(__file__), "..", "..")
    return os.path.join(root_path, *root_file_path)


def read_file(*root_file_path: str) -> str:
    r"""Read the contens of the file

    Args:
        root_file_path (\*str): path of the file to read from the root project directory

    Returns:
        str: contents of the file
    """
    with open(get_abs_path(*root_file_path), "r", encoding="utf-8") as in_file:
        text = in_file.read().strip()
    return text


def read_md(file_name: str) -> str:
    """Read the contens of a markdown file.
    The path is data/markdown.
    It also will replace the following parts of the text:

    - {channel_tag} -> config_map['meme']['channel_tag']
    - {bot_tag} -> config_map['bot_tag']

    Args:
        file_name (str): name of the file

    Returns:
        str: contents of the file
    """
    text = read_file("data", "markdown", file_name + ".md")
    text = text.replace("{channel_tag}", escape_markdown(config_map['meme']['channel_tag'], version=2))
    text = text.replace("{bot_tag}", escape_markdown(config_map['bot_tag'], version=2))
    return text


def load_configuration(path: str, load_default: bool = True, force_load: bool = False) -> dict:
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
            conf.update(yaml.load(conf_file, Loader=yaml.SafeLoader))
    if force_load or os.path.exists(path):
        with open(path, 'r', encoding="utf-8") as conf_file:
            conf.update(yaml.load(conf_file, Loader=yaml.SafeLoader))
    return conf


def read_env(config: dict):
    """Reads the enviroment variables and stores the values in the config dict.
    Any key already present will be overwritten

    Args:
        config: configuration dictionary
    """
    new_vars = {}
    config['test'] = config['test'] if config.get('test', False) else {}
    config['meme'] = config['meme'] if config.get('meme', False) else {}
    if os.path.exists(get_abs_path(".env")):
        envre = re.compile(r'''^([^\s=]+)=(?:[\s"']*)(.+?)(?:[\s"']*)$''')
        with open(get_abs_path(".env")) as env:
            for line in env:
                match = envre.match(line)
                if match is not None:
                    new_vars[match.group(1).lower()] = match.group(2)

    for key in os.environ:
        new_vars[key.lower()] = os.getenv(key)

    for key in new_vars:
        if key.startswith("test_"):
            config['test'][key[5:]] = new_vars[key]
        elif key.startswith("meme_"):
            config['meme'][key[5:]] = new_vars[key]
        else:
            config[key] = new_vars[key]


def validate_config_types(config: dict):
    """Validates the enviroment variables, casting them when necessary

    Args:
        config: config_map
    """
    meme_confs = ((int, 'channel_group_id'), (int, 'channel_id'), (bool, 'comments'), (int, 'group_id'), (int, 'n_votes'),
                 (int, 'remove_after_h'), (bool, 'reset_on_load'), (int, 'report_wait_mins'), (bool, 'tag'))
    for meme_conf in meme_confs:
        config['meme'][meme_conf[1]] = meme_conf[0](config['meme'][meme_conf[1]])


# Read the local configuration. First, load the .default file, than override it with any non .default file
settings_path = get_abs_path("config", "settings.yaml")
config_map = load_configuration(settings_path, force_load=True)

reaction_path = get_abs_path("data", "yaml", "reactions.yaml")
config_reactions = load_configuration(reaction_path)

read_env(config_map)
validate_config_types(config_map)
