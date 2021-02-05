"""Handles the management of databases"""
import logging
from typing import Tuple
import sqlite3
from modules.data.data_reader import get_abs_path, read_file

logger = logging.getLogger(__name__)


def dict_factory(cursor: sqlite3.Cursor, row: sqlite3.Row) -> dict:
    """Makes so that the cursor is a list of dictionaries with column names as keys

    Args:
        cursor (sqlite3.Cursor): cursor generated by the database
        row (sqlite3.Row): rows of the database

    Returns:
        dict: structure of the database used used by the cursor
    """
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


class DbManager():
    """Class that handles the management of databases
    """

    @staticmethod
    def get_db() -> Tuple[sqlite3.Connection, sqlite3.Cursor]:
        """Creates the connection to the database. It can be sqlite or postgres

        Returns:
            Tuple[sqlite3.Connection, sqlite3.Cursor]: sqlite database connection and cursor
        """
        db_path = get_abs_path("data", "db", "sqlite.db")
        conn = sqlite3.connect(db_path)
        conn.row_factory = dict_factory
        cur = conn.cursor()
        return conn, cur

    @staticmethod
    def query_from_file(*file_path: str):
        """Commits all the queries in the specified file. The queries must be separated by a ----- string
        Should not be used to select something

        Args:
            file_path (str): path of the text file containing the queries
        """
        conn, cur = DbManager.get_db()
        queries = read_file(*file_path).split("-----")
        for query in queries:
            cur.execute(query)
        conn.commit()
        cur.close()
        conn.close()

    @staticmethod
    def query_from_string(*queries: str):
        """Commits all the queries in the string
        Should not be used to select something

        Args:
            queries (str): tuple of queries
        """
        conn, cur = DbManager.get_db()
        for query in queries:
            cur.execute(query)

        conn.commit()
        cur.close()
        conn.close()

    @staticmethod
    def select_from(table_name: str, select: str = "*", where: str = "", where_args: tuple = None, order_by: str = "") -> list:
        """Returns the result of a SELECT select FROM table_name [WHERE where (with where_args)]

        Args:
            table_name (str): name of the table used in the FROM
            select (str, optional): columns considered for the query. Defaults to "*".
            where (str, optional): where clause, with %s placeholders for the where_args. Defaults to "".
            where_args (tuple, optional): args used in the where clause. Defaults to None.

        Returns:
            list: rows from the select
        """
        conn, cur = DbManager.get_db()

        where = where.replace("%s", "?")

        sql_query = f"SELECT {select} FROM {table_name} "

        if where:
            sql_query += f"WHERE {where} "  
            if order_by:
                sql_query += f"ORDER BY {order_by} "               
            if where_args:
                try:
                    cur.execute(sql_query, where_args)
                except sqlite3.Error as e:
                    logger.error(str(e))
            else:
                try:
                    cur.execute(sql_query)
                except sqlite3.Error as e:
                    logger.error(str(e))
        else:
            if order_by:
                sql_query += f"ORDER BY {order_by} "  
            try:
                cur.execute(sql_query)
            except sqlite3.Error as e:
                logger.error(str(e))
        
        query_result = cur.fetchall()
        cur.close()
        conn.close()
        return query_result

    @staticmethod
    def count_from(table_name: str, select: str = "*", where: str = "", where_args: tuple = None) -> int:
        """Returns the number of rows from SELECT COUNT(*) FROM table_name WHERE where

        Args:
            table_name (str): name of the table used in the FROM
            select (str, optional): columns considered for the query. Defaults to "*".
            where (str, optional): where clause, with %s placeholders for the where_args. Defaults to "".
            where_args (tuple, optional): args used in the where clause. Defaults to None.

        Returns:
            int: number of rows
        """
        conn, cur = DbManager.get_db()

        where = where.replace("%s", "?")

        if where:
            if where_args:
                try:
                    cur.execute(f"SELECT COUNT({select}) as number FROM {table_name} WHERE {where}", where_args)
                except sqlite3.Error as e:
                    logger.error(str(e))
            else:
                try:
                    cur.execute(f"SELECT COUNT({select}) as number FROM {table_name} WHERE {where}")
                except sqlite3.Error as e:
                    logger.error(str(e))
        else:
            try:
                cur.execute(f"SELECT COUNT({select}) as number FROM {table_name}")
            except sqlite3.Error as e:
                logger.error(str(e))

        query_result = cur.fetchall()
        cur.close()
        conn.close()
        return query_result[0]['number']

    @staticmethod
    def insert_into(table_name: str, values: tuple, columns: tuple = ""):
        """Inserts the specified values in the database

        Args:
            table_name (str): name of the table used in the INSERT INTO
            values (tuple): values to be inserted
            columns (tuple, optional): columns that will be inserted, as a tuple of strings. Defaults to None.
        """
        conn, cur = DbManager.get_db()


        placeholders = ", ".join(["?" for _ in values])

        if columns:
            columns = "(" + ", ".join(columns) + ")"

        try:
            cur.execute(f"INSERT INTO {table_name} {columns} VALUES ({placeholders})", values)
        except sqlite3.Error as e:
            print("[error] select_start_from_where: " + str(e))

        conn.commit()
        cur.close()
        conn.close()

    @staticmethod
    def delete_from(table_name: str, where: str = "", where_args: tuple = None):
        """Deletes the rows from the specified table, where the condition, when set, is satisfied
        Execute "DELETE FROM table_name [WHERE where (with where_args)]"

        Args:
            table_name (str): name of the table used in the DELETE FROM
            where (str, optional): where clause, with %s placeholders for the where args. Defaults to "".
            where_args (tuple, optional): args used in the where clause. Defaults to None.
        """
        conn, cur = DbManager.get_db()

        where = where.replace("%s", "?")

        if where:
            if where_args:
                try:
                    cur.execute(f"DELETE FROM {table_name} WHERE {where}", where_args)
                except sqlite3.Error as e:
                    logger.error(str(e))
            else:
                try:
                    cur.execute(f"DELETE FROM {table_name} WHERE {where}")
                except sqlite3.Error as e:
                    logger.error(str(e))
        else:
            try:
                cur.execute(f"DELETE FROM {table_name}")
            except sqlite3.Error as e:
                logger.error(str(e))

        conn.commit()
        cur.close()
        conn.close()
