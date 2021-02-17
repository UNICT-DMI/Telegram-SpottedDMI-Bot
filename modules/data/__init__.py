"""Modules that work with the data section"""
from modules.data.data_reader import config_map
from .db_manager import DbManager
from .pending_post import PendingPost
from .published_post import PublishedPost
from .post_data import PostData
from .report import Report
from .user import User

if config_map['meme']['reset_on_load']:
    DbManager.query_from_file("data", "db", "meme_db_del.sql")
DbManager.query_from_file("data", "db", "meme_db_init.sql")
