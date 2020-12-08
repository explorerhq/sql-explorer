# -*- coding: utf-8 -*-
from unittest.mock import patch

from django.core.cache import cache
from django.db import connection
from django.test import TestCase

from explorer.app_settings import EXPLORER_DEFAULT_CONNECTION as CONN
from explorer import schema


class TestSchemaInfo(TestCase):

    def setUp(self):
        cache.clear()

    @patch('explorer.schema._get_includes')
    @patch('explorer.schema._get_excludes')
    def test_schema_info_returns_valid_data(self, mocked_excludes,
                                            mocked_includes):
        mocked_includes.return_value = None
        mocked_excludes.return_value = []
        res = schema.schema_info(CONN)
        assert mocked_includes.called  # sanity check: ensure patch worked
        tables = [x[0] for x in res]
        self.assertIn('explorer_query', tables)

    @patch('explorer.schema._get_includes')
    @patch('explorer.schema._get_excludes')
    def test_table_exclusion_list(self, mocked_excludes, mocked_includes):
        mocked_includes.return_value = None
        mocked_excludes.return_value = ('explorer_',)
        res = schema.schema_info(CONN)
        tables = [x[0] for x in res]
        self.assertNotIn('explorer_query', tables)

    @patch('explorer.schema._get_includes')
    @patch('explorer.schema._get_excludes')
    def test_app_inclusion_list(self, mocked_excludes, mocked_includes):
        mocked_includes.return_value = ('auth_',)
        mocked_excludes.return_value = []
        res = schema.schema_info(CONN)
        tables = [x[0] for x in res]
        self.assertNotIn('explorer_query', tables)
        self.assertIn('auth_user', tables)

    @patch('explorer.schema._get_includes')
    @patch('explorer.schema._get_excludes')
    def test_app_inclusion_list_excluded(self, mocked_excludes,
                                         mocked_includes):
        # Inclusion list "wins"
        mocked_includes.return_value = ('explorer_',)
        mocked_excludes.return_value = ('explorer_',)
        res = schema.schema_info(CONN)
        tables = [x[0] for x in res]
        self.assertIn('explorer_query', tables)

    @patch('explorer.schema._include_views')
    def test_app_include_views(self, mocked_include_views):
        database_view = setup_sample_database_view()
        mocked_include_views.return_value = True
        res = schema.schema_info(CONN)
        tables = [x[0] for x in res]
        self.assertIn(database_view, tables)

    @patch('explorer.schema._include_views')
    def test_app_exclude_views(self, mocked_include_views):
        database_view = setup_sample_database_view()
        mocked_include_views.return_value = False
        res = schema.schema_info(CONN)
        tables = [x[0] for x in res]
        self.assertNotIn(database_view, tables)

    @patch('explorer.schema.do_async')
    def test_builds_async(self, mocked_async_check):
        mocked_async_check.return_value = True
        self.assertIsNone(schema.schema_info(CONN))
        res = schema.schema_info(CONN)
        tables = [x[0] for x in res]
        self.assertIn('explorer_query', tables)


def setup_sample_database_view():
    with connection.cursor() as cursor:
        cursor.execute(
            "CREATE VIEW IF NOT EXISTS v_explorer_query AS SELECT title, "
            "sql from explorer_query"
        )
    return 'v_explorer_query'
