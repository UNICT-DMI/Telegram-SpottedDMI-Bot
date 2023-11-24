"""Read data from files"""
import os
from importlib import resources

from telegram.helpers import escape_markdown

from .config import Config


def get_abs_path(*root_file_path: str) -> str:
    """Get the abs path from the root directory of the project to the requested path

    Args:
        root_file_path: path from the root project directory

    Returns:
        corresponding abs path
    """
    return os.path.join(resources.files("spotted"), *root_file_path)


def read_file(*root_file_path: str) -> str:
    """Read the contents of the file

    Args:
        root_file_path: path of the file to read from the root project directory

    Returns:
        contents of the file
    """
    with open(get_abs_path(*root_file_path), "r", encoding="utf-8") as in_file:
        text = in_file.read().strip()
    return text


def read_md(file_name: str) -> str:
    """Read the contents of a markdown file.
    The path is data/markdown.
    It also will replace the following parts of the text:

    - {channel_tag} -> Config.settings['post']['channel_tag']
    - {bot_tag}     -> Config.settings['bot_tag']

    Args:
        file_name: name of the file

    Returns:
        contents of the file
    """
    text = read_file("config", "markdown", f"{file_name}.md")
    text = text.replace("{channel_tag}", escape_markdown(Config.post_get("channel_tag"), version=2))
    text = text.replace("{bot_tag}", escape_markdown(Config.settings_get("bot_tag"), version=2))
    return text
