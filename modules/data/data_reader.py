"""Read data from files"""
import os
import yaml


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
    """Read the contens of a markdown file. The path is data/markdown

    Args:
        file_name (str): name of the file

    Returns:
        str: contents of the file
    """
    return read_file("data", "markdown", file_name + ".md")


with open(get_abs_path("config", "settings.yaml"), 'r') as yaml_config:
    config_map = yaml.load(yaml_config, Loader=yaml.SafeLoader)
