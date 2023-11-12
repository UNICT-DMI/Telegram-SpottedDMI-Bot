"""Modules that work with the data section"""
from telegram.ext import Application

from .config import Config
from .data_reader import get_abs_path, read_md
from .db_manager import DbManager
from .pending_post import PendingPost
from .post_data import PostData
from .published_post import PublishedPost
from .report import Report
from .user import User


def init_db():
    """Initialize the database.
    If the debug.reset_on_load setting is True, it will delete the database and create a new one.
    """
    if Config.settings_get("debug", "reset_on_load"):
        DbManager.query_from_file("config", "db", "post_db_del.sql")
    DbManager.query_from_file("config", "db", "post_db_init.sql")
