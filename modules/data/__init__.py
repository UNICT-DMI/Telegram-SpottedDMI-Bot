"""Modules that work with the data section"""
from .config import Config
from .data_reader import get_abs_path, read_md
from .db_manager import DbManager
from .pending_post import PendingPost
from .post_data import PostData
from .published_post import PublishedPost
from .report import Report
from .user import User

if Config.settings_get('debug', 'reset_on_load'):
    DbManager.query_from_file("data", "db", "meme_db_del.sql")
DbManager.query_from_file("data", "db", "meme_db_init.sql")
