# pylint: disable=unused-argument,redefined-outer-name
"""Test all the modules related to data management"""
import pytest
import yaml

from spotted.data import DbManager

TABLE_NAME = "test_table"


@pytest.fixture(scope="class")
def db_results(create_test_db: DbManager) -> dict:
    """Called at the beginning of the testing session.
    Creates initializes the database

    Yields:
        Iterator[dict]: dictionary containing the results for the test queries
    """
    create_test_db.row_factory = (
        lambda cursor, row: list(row) if cursor.description[0][0] != "number" else {"number": row[0]}
    )
    create_test_db.query_from_file("config/db/db_test.sql")

    with open("tests/unit/db_results.yaml", "r", encoding="utf-8") as yaml_config:
        results = yaml.load(yaml_config, Loader=yaml.SafeLoader)

    yield results

    create_test_db.query_from_string("DROP TABLE IF EXISTS test_table;")


class TestDB:
    """Test the DBManager class"""

    def test_get_db(self, db_results):
        """Tests the get_db function for the database"""

        conn, cur = DbManager.get_db()

        assert conn is not None
        assert cur is not None

    def test_query_from_string(self, db_results):
        """Tests the query_from_string function for the database"""

        DbManager.query_from_string(
            "DROP TABLE IF EXISTS temp;", "CREATE TABLE temp(id int NOT NULL, PRIMARY KEY (id));"
        )

        assert DbManager.count_from(table_name="temp") == 0

        DbManager.query_from_string("DROP TABLE temp;")

    def test_select_from(self, db_results):
        """Tests the select_from function of the database"""

        query_result = DbManager.select_from(table_name=TABLE_NAME, where="id = %s or id = %s", where_args=(2, 3))
        assert query_result == db_results["select_from1"]

        query_result = DbManager.select_from(table_name=TABLE_NAME, select="id, name", where=" id = 1")
        assert query_result == db_results["select_from2"]

        query_result = DbManager.select_from(table_name=TABLE_NAME, select="id")
        assert query_result == db_results["select_from3"]

    def test_count_from(self, db_results):
        """Tests the count_from function of the database"""

        query_result = DbManager.count_from(table_name=TABLE_NAME, where="id = %s or id = %s", where_args=(2, 3))
        assert query_result == db_results["count_from1"]

        query_result = DbManager.count_from(table_name=TABLE_NAME, select="name", where=" id = 1")
        assert query_result == db_results["count_from2"]

        query_result = DbManager.count_from(table_name=TABLE_NAME, select="id")
        assert query_result == db_results["count_from3"]

    def test_insert_into(self, db_results):
        """Tests the insert_into function of the database"""

        DbManager.insert_into(table_name=TABLE_NAME, values=(10, "test_insert1", "none"))
        DbManager.insert_into(
            table_name=TABLE_NAME, values=(11, "test_insert2", "none"), columns=("id", "name", "surname")
        )
        DbManager.insert_into(
            table_name=TABLE_NAME,
            values=((12, "test_insert3", "none"), (13, "test_insert4", "none")),
            columns=("id", "name", "surname"),
            multiple_rows=True,
        )
        query_result = DbManager.select_from(table_name=TABLE_NAME, where="id >= %s", where_args=(10,))
        DbManager.delete_from(table_name=TABLE_NAME, where=" id >= 10")

        assert query_result == db_results["insert_into"]

    def test_update_from(self, db_results):
        """Tests the update_from function of the database"""
        DbManager.update_from(table_name=TABLE_NAME, set_clause="surname = %s", args=("none",))
        DbManager.update_from(
            table_name=TABLE_NAME, set_clause="name = %s", where="id IN (%s, %s)", args=("modif", 1, 4)
        )
        query_result = DbManager.select_from(table_name=TABLE_NAME, order_by="id")

        assert query_result == db_results["update_from"]

    def test_delete_from(self, db_results):
        """Tests the delete_from function of the database"""

        DbManager.query_from_string(
            """DROP TABLE IF EXISTS temp;""",
            """CREATE TABLE temp(
                                    id int NOT NULL,
                                    PRIMARY KEY (id)
                                    );""",
        )
        for i in range(5):
            DbManager.insert_into(table_name="temp", values=(i,))

        count = DbManager.count_from(table_name="temp", where="id >= %s", where_args=(-1,))
        assert count == 5

        DbManager.delete_from(table_name="temp", where=" id >= %s", where_args=(3,))
        count = DbManager.count_from(table_name="temp", where="id >= %s", where_args=(-1,))
        assert count == 3

        DbManager.delete_from(table_name="temp")
        count = DbManager.count_from(table_name="temp", where="id >= %s", where_args=(-1,))
        assert count == 0

        DbManager.query_from_string("DROP TABLE temp;")
