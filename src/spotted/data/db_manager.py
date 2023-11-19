"""Handles the management of databases"""
import logging
import os
import sqlite3

from .config import Config
from .data_reader import read_file

logger = logging.getLogger(__name__)


class DbManager:
    """Class that handles the management of databases"""

    @staticmethod
    def row_factory(cursor: sqlite3.Cursor, row: dict) -> dict:
        """Converts the rows from the database into a dictionary

        Args:
            cursor: database cursor
            row: row from the database

        Returns:
            dictionary containing the row. The keys are the column names
        """
        return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

    @classmethod
    def __query_execute(
        cls, cur: sqlite3.Cursor, query: str, args: tuple | None = None, error_str: str = "", is_many: bool = False
    ):
        """Materially executes the requested query, while also catching and logging any exception that may be thrown

        Args:
            cur: database cursor
            query: query to execute. It may contain ? placeholders
            args: tuple of values that will replace the placeholders
            error_str: name of the method that caused the exception
            is_many: whether to use the :func:`sqlite3.Cursor.executemany` function
        """
        query_func = cur.executemany if is_many else cur.execute

        try:
            if args:
                query_func(query, args)
            else:
                query_func(query)  # type: ignore
        except sqlite3.Error as ex:
            logger.error("DbManager.%s(): %s", error_str, ex)

    @classmethod
    def get_db(cls) -> tuple[sqlite3.Connection, sqlite3.Cursor]:
        """Creates the connection to the database. It can be sqlite or postgres

        Returns:
            sqlite database connection and cursor
        """
        db_file = Config.debug_get("db_file")
        if not os.path.exists(db_file):
            with open(db_file, "w", encoding="utf-8"):
                pass
        conn = sqlite3.connect(db_file, detect_types=sqlite3.PARSE_DECLTYPES)
        conn.row_factory = cls.row_factory
        cur = conn.cursor()
        return conn, cur

    @classmethod
    def query_from_file(cls, *file_path: str):
        """Commits all the queries in the specified file. The queries must be separated by a ----- string
        Should not be used to select something

        Args:
            file_path: path of the text file containing the queries
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
            queries: tuple of queries
        """
        conn, cur = cls.get_db()
        for query in queries:
            cls.__query_execute(cur=cur, query=query, error_str="query_from_string")

        conn.commit()
        cur.close()
        conn.close()

    @classmethod
    def select_from(
        cls,
        table_name: str,
        select: str = "*",
        where: str = "",
        where_args: tuple | None = None,
        group_by: str = "",
        order_by: str = "",
    ) -> list:
        """Returns the results of a query.
        Executes "SELECT select FROM table_name [WHERE where (with where_args)] [GROUP_BY group_by] [ORDER BY order_by]"

        Args:
            table_name: name of the table used in the FROM
            select: columns considered for the query
            where: where clause, with %s placeholders for the where_args
            where_args: args used in the where clause
            group_by: group by clause
            order_by: order by clause

        Returns:
            rows from the select
        """
        conn, cur = cls.get_db()

        where = where.replace("%s", "?")
        where = f"WHERE {where}" if where else ""
        group_by = f"GROUP BY {group_by}" if group_by else ""
        order_by = f"ORDER BY {order_by}" if order_by else ""

        cls.__query_execute(
            cur=cur,
            query=f"SELECT {select} FROM {table_name} {where} {group_by} {order_by}",
            args=where_args,
            error_str="select_from",
        )

        query_result = cur.fetchall()
        conn.commit()
        cur.close()
        conn.close()
        return query_result

    @classmethod
    def count_from(cls, table_name: str, select: str = "*", where: str = "", where_args: tuple | None = None) -> int:
        """Returns the number of rows found with the query.
        Executes "SELECT COUNT(select) FROM table_name [WHERE where (with where_args)]"

        Args:
            table_name: name of the table used in the FROM
            select: columns considered for the query
            where: where clause, with %s placeholders for the where_args
            where_args: args used in the where clause

        Returns:
            number of rows
        """
        conn, cur = cls.get_db()

        where = where.replace("%s", "?")
        where = f"WHERE {where}" if where else ""

        cls.__query_execute(
            cur=cur,
            query=f"SELECT COUNT({select}) as number FROM {table_name} {where}",
            args=where_args,
            error_str="count_from",
        )

        query_result = cur.fetchall()
        conn.commit()
        cur.close()
        conn.close()
        return query_result[0]["number"] if len(query_result) > 0 else None

    @classmethod
    def insert_into(cls, table_name: str, values: tuple, columns: tuple | str = "", multiple_rows: bool = False):
        """Inserts the specified values in the database.
        Executes "INSERT INTO table_name ([columns]) VALUES (placeholders)"

        Args:
            table_name: name of the table used in the INSERT INTO
            values: values to be inserted. If multiple_rows is true, tuple of tuples of values to be inserted
            columns: columns that will be inserted, as a tuple of strings
            multiple_rows: whether or not multiple rows will be inserted at the same time
        """
        conn, cur = cls.get_db()

        if multiple_rows:
            placeholders = ", ".join(["?" for _ in values[0]])
        else:
            placeholders = ", ".join(["?" for _ in values])

        if columns:
            columns = "(" + ", ".join(columns) + ")"

        cls.__query_execute(
            cur=cur,
            query=f"INSERT INTO {table_name} {columns} VALUES ({placeholders})",
            args=values,
            error_str="insert_into",
            is_many=multiple_rows,
        )

        conn.commit()
        cur.close()
        conn.close()

    @classmethod
    def update_from(cls, table_name: str, set_clause: str, where: str = "", args: tuple | None = None):
        """Updates the rows from the specified table, where the condition, when set, is satisfied.
        Executes "UPDATE table_name SET set_clause (with args) [WHERE where (with args)]"

        Args:
            table_name: name of the table used in the DELETE FROM
            set_clause: set clause, with %s placeholders
            where: where clause, with %s placeholders for the where args
            args: args used both in the set clause and in the where clause, in this order
        """
        conn, cur = cls.get_db()

        set_clause = set_clause.replace("%s", "?")
        where = where.replace("%s", "?")
        where = f"WHERE {where}" if where else ""

        cls.__query_execute(
            cur=cur, query=f"UPDATE {table_name} SET {set_clause} {where}", args=args, error_str="update_from"
        )

        conn.commit()
        cur.close()
        conn.close()

    @classmethod
    def delete_from(cls, table_name: str, where: str = "", where_args: tuple | None = None):
        """Deletes the rows from the specified table, where the condition, when set, is satisfied.
        Executes "DELETE FROM table_name [WHERE where (with where_args)]"

        Args:
            table_name: name of the table used in the DELETE FROM
            where: where clause, with %s placeholders for the where args
            where_args: args used in the where clause
        """
        conn, cur = cls.get_db()

        where = where.replace("%s", "?")
        where = f"WHERE {where}" if where else ""

        cls.__query_execute(
            cur=cur, query=f"DELETE FROM {table_name} {where}", args=where_args, error_str="delete_from"
        )

        conn.commit()
        cur.close()
        conn.close()
