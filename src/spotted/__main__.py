"""Main module"""
import argparse
from typing import TYPE_CHECKING

from spotted import run_bot
from spotted.data import Config

try:
    from spotted._version import __version__
except ImportError:
    __version__ = "0.0.0"

if TYPE_CHECKING:

    class SpottedArgs(argparse.Namespace):
        """Type hinting for the command line arguments"""

        settings: str
        autoreplies: str


def parse_args() -> "SpottedArgs":
    """Parse the command line arguments

    Returns:
        data structure containing the command line arguments
    """
    parser = argparse.ArgumentParser(description="Telegram Spotted DMI bot")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("-s", "--settings", help="Path to the settings file", default="settings.yaml")
    parser.add_argument("-a", "--autoreplies", help="Path to the autoreplies file", default="autoreplies.yaml")
    return parser.parse_args()


def main():
    """Main function"""
    args = parse_args()
    Config.SETTINGS_PATH = args.settings
    Config.AUTOREPLIES_PATH = args.autoreplies
    run_bot()


if __name__ == "__main__":
    main()
