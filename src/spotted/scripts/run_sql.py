import argparse
import os
from typing import TYPE_CHECKING

from spotted.data import Config, DbManager

if TYPE_CHECKING:

    class RunSQLArgs(argparse.Namespace):
        """Type hinting for the command line arguments"""

        sql_file: str
        db_file: str


def parse_args() -> "RunSQLArgs":
    """Parse the command line arguments

    Returns:
        data structure containing the command line arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "sql_file",
        type=str,
        help="Path to the SQL file. Multiple queries must be separated by a ';'",
    )
    parser.add_argument("db_file", type=str, help="Path to the database file")
    return parser.parse_args()


def main():
    """Main function"""
    args = parse_args()
    print(os.getcwd())
    Config.override_settings({"debug": {"db_file": args.db_file}})
    conn, cur = DbManager.get_db()

    with open(args.sql_file, "r", encoding="utf-8") as sql_file:
        conn.executescript(sql_file.read())

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
