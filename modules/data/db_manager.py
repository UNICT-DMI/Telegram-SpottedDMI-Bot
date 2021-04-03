"""Handles the management of databases"""
import logging
from typing import Tuple
import sqlite3
from modules.data.data_reader import get_abs_path, read_file

logger = logging.getLogger(__name__)


class DbManager():
    """Class that handles the management of databases
    """
    row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

    @classmethod
    def __query_execute(cls, cur: sqlite3.Cursor, query: str, args: tuple = None, error_str: str = "", is_many: bool = False):
        """Materially executes the requested query, while also catching and logging any exception that may be thrown

        Args:
            cur (sqlite3.Cursor): database cursor
            query (str): query to execute. It may contain ? placehorders
            args (tuple, optional): tuple of values that will replace the placeholders. Defaults to None.
            error_str (str, optional): name of the method that caused the exception. Defaults to "".
            is_many (bool, optional): whether to use the :func:`sqlite3.Cursor.executemany` function. Defaults to False.
        """
        query_func = cur.executemany if is_many else cur.execute

        try:
            if args:
                query_func(query, args)
            else:
                query_func(query)
        except sqlite3.Error as e:
            logger.error("DbManager.%s(): %s", error_str, e)

    @classmethod
    def get_db(cls) -> Tuple[sqlite3.Connection, sqlite3.Cursor]:
        """Creates the connection to the database. It can be sqlite or postgres

        Returns:
            Tuple[sqlite3.Connection, sqlite3.Cursor]: sqlite database connection and cursor
        """
        db_path = get_abs_path("data", "db", "sqlite.db")
        conn = sqlite3.connect(db_path)
        conn.row_factory = cls.row_factory
        cur = conn.cursor()
        return conn, cur

    @classmethod
    def query_from_file(cls, *file_path: str):
        """Commits all the queries in the specified file. The queries must be separated by a ----- string
        Should not be used to select something

        Args:
            file_path (str): path of the text file containing the queries
        """
        conn, cur = cls.get_db()
        queries = read_file(*file_path).split("-----")
        for query in queries:
            cls.__query_execute(cur=cur, query=query, error_str="query_from_file")
        conn.commit()
        cur.close()
        conn.close()

    @classmethod
    def query_from_string(cls, *queries: str):
        """Commits all the queries in the string
        Should not be used to select something

        Args:
            queries (str): tuple of queries
        """
        conn, cur = cls.get_db()
        for query in queries:
            cls.__query_execute(cur=cur, query=query, error_str="query_from_string")

        conn.commit()
        cur.close()
        conn.close()

    @classmethod
    def select_from(cls,
                    table_name: str,
                    select: str = "*",
                    where: str = "",
                    where_args: tuple = None,
                    group_by: str = "",
                    order_by: str = "") -> list:
        """Returns the results of a query.
        Executes "SELECT select FROM table_name [WHERE where (with where_args)] [GROUP_BY group_by] [ORDER BY order_by]"

        Args:
            table_name (str): name of the table used in the FROM
            select (str, optional): columns considered for the query. Defaults to "*".
            where (str, optional): where clause, with %s placeholders for the where_args. Defaults to "".
            where_args (tuple, optional): args used in the where clause. Defaults to None.
            group_by (str, optional): group by clause. Defaults to "".
            order_by (str, optional): order by clause. Defaults to "".

        Returns:
            list: rows from the select
        """
        conn, cur = cls.get_db()

        where = where.replace("%s", "?")
        where = f"WHERE {where}" if where else ""
        group_by = f"GROUP BY {group_by}" if group_by else ""
        order_by = f"ORDER BY {order_by}" if order_by else ""

        cls.__query_execute(cur=cur,
                            query=f"SELECT {select} FROM {table_name} {where} {group_by} {order_by}",
                            args=where_args,
                            error_str="select_from")

        query_result = cur.fetchall()
        conn.commit()
        cur.close()
        conn.close()
        return query_result

    @classmethod
    def count_from(cls, table_name: str, select: str = "*", where: str = "", where_args: tuple = None) -> int:
        """Returns the number of rows found with the query.
        Executes "SELECT COUNT(select) FROM table_name [WHERE where (with where_args)]"

        Args:
            table_name (str): name of the table used in the FROM
            select (str, optional): columns considered for the query. Defaults to "*".
            where (str, optional): where clause, with %s placeholders for the where_args. Defaults to "".
            where_args (tuple, optional): args used in the where clause. Defaults to None.

        Returns:
            int: number of rows
        """
        conn, cur = cls.get_db()

        where = where.replace("%s", "?")
        where = f"WHERE {where}" if where else ""

        cls.__query_execute(cur=cur,
                            query=f"SELECT COUNT({select}) as number FROM {table_name} {where}",
                            args=where_args,
                            error_str="count_from")

        query_result = cur.fetchall()
        conn.commit()
        cur.close()
        conn.close()
        return query_result[0]['number'] if len(query_result) > 0 else None

    @classmethod
    def insert_into(cls, table_name: str, values: tuple, columns: tuple = "", multiple_rows: bool = False):
        """Inserts the specified values in the database.
        Executes "INSERT INTO table_name ([columns]) VALUES (placeholders)"

        Args:
            table_name (str): name of the table used in the INSERT INTO
            values (tuple): values to be inserted. If multiple_rows is true, tuple of tuples of values to be inserted
            columns (tuple, optional): columns that will be inserted, as a tuple of strings. Defaults to None.
            multiple_rows (bool): whether or not multiple rows will be inserted at the same time
        """
        conn, cur = cls.get_db()

        if multiple_rows:
            placeholders = ", ".join(["?" for _ in values[0]])
        else:
            placeholders = ", ".join(["?" for _ in values])

        if columns:
            columns = "(" + ", ".join(columns) + ")"

        cls.__query_execute(cur=cur,
                            query=f"INSERT INTO {table_name} {columns} VALUES ({placeholders})",
                            args=values,
                            error_str="insert_into",
                            is_many=multiple_rows)

        conn.commit()
        cur.close()
        conn.close()

    @classmethod
    def delete_from(cls, table_name: str, where: str = "", where_args: tuple = None):
        """Deletes the rows from the specified table, where the condition, when set, is satisfied.
        Executes "DELETE FROM table_name [WHERE where (with where_args)]"

        Args:
            table_name (str): name of the table used in the DELETE FROM
            where (str, optional): where clause, with %s placeholders for the where args. Defaults to "".
            where_args (tuple, optional): args used in the where clause. Defaults to None.
        """
        conn, cur = cls.get_db()

        where = where.replace("%s", "?")
        where = f"WHERE {where}" if where else ""

        cls.__query_execute(cur=cur, query=f"DELETE FROM {table_name} {where}", args=where_args, error_str="delete_from")

        conn.commit()
        cur.close()
        conn.close()
