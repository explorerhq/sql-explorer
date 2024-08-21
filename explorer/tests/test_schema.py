from unittest.mock import patch

from django.core.cache import cache
from django.db import connection
from django.test import TestCase

from explorer import schema
from explorer.ee.db_connections.utils import default_db_connection


def conn():
    return default_db_connection()


class TestSchemaInfo(TestCase):

    def setUp(self):
        cache.clear()

    @patch("explorer.schema._get_includes")
    @patch("explorer.schema._get_excludes")
    def test_schema_info_returns_valid_data(self, mocked_excludes,
                                            mocked_includes):
        mocked_includes.return_value = None
        mocked_excludes.return_value = []
        res = schema.schema_info(conn())
        assert mocked_includes.called  # sanity check: ensure patch worked
        tables = [x[0] for x in res]
        self.assertIn("explorer_query", tables)

        json_res = schema.schema_json_info(conn())
        self.assertListEqual(list(json_res.keys()), tables)

    @patch("explorer.schema._get_includes")
    @patch("explorer.schema._get_excludes")
    def test_table_exclusion_list(self, mocked_excludes, mocked_includes):
        mocked_includes.return_value = None
        mocked_excludes.return_value = ("explorer_",)
        res = schema.schema_info(conn())
        tables = [x[0] for x in res]
        self.assertNotIn("explorer_query", tables)

    @patch("explorer.schema._get_includes")
    @patch("explorer.schema._get_excludes")
    def test_app_inclusion_list(self, mocked_excludes, mocked_includes):
        mocked_includes.return_value = ("auth_",)
        mocked_excludes.return_value = []
        res = schema.schema_info(conn())
        tables = [x[0] for x in res]
        self.assertNotIn("explorer_query", tables)
        self.assertIn("auth_user", tables)

    @patch("explorer.schema._get_includes")
    @patch("explorer.schema._get_excludes")
    def test_app_inclusion_list_excluded(self, mocked_excludes,
                                         mocked_includes):
        # Inclusion list "wins"
        mocked_includes.return_value = ("explorer_",)
        mocked_excludes.return_value = ("explorer_",)
        res = schema.schema_info(conn())
        tables = [x[0] for x in res]
        self.assertIn("explorer_query", tables)

    @patch("explorer.schema._include_views")
    def test_app_include_views(self, mocked_include_views):
        database_view = setup_sample_database_view()
        mocked_include_views.return_value = True
        res = schema.schema_info(conn())
        tables = [x[0] for x in res]
        self.assertIn(database_view, tables)

    @patch("explorer.schema._include_views")
    def test_app_exclude_views(self, mocked_include_views):
        database_view = setup_sample_database_view()
        mocked_include_views.return_value = False
        res = schema.schema_info(conn())
        tables = [x[0] for x in res]
        self.assertNotIn(database_view, tables)

    def test_transform_to_json(self):
        schema_info = [
            ("table1", [("col1", "type1"), ("col2", "type2")]),
            ("table2", [("col1", "type1"), ("col2", "type2")]),
        ]
        json_schema = schema.transform_to_json_schema(schema_info)
        self.assertEqual(json_schema, {
            "table1": ["col1", "col2"],
            "table2": ["col1", "col2"],
        })


def setup_sample_database_view():
    with connection.cursor() as cursor:
        cursor.execute(
            "CREATE VIEW IF NOT EXISTS v_explorer_query AS SELECT title, "
            "sql from explorer_query"
        )
    return "v_explorer_query"
