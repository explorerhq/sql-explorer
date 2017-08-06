from django.test import TestCase
from django.core.cache import cache
from explorer.app_settings import EXPLORER_DEFAULT_CONNECTION as CONN
from explorer import schema
from mock import patch
import sys


# Totally unclear why this is necessary but py2 and py3
# want these patches slightly differently.
PY3 = sys.version_info[0] == 3
if PY3:
    patch_location = 'schema.'
else:
    patch_location = 'explorer.schema.'


class TestSchemaInfo(TestCase):

    def setUp(self):
        cache.clear()

    @patch(patch_location + '_get_includes')
    @patch(patch_location + '_get_excludes')
    def test_schema_info_returns_valid_data(self, mocked_excludes, mocked_includes):
        mocked_includes.return_value = None
        mocked_excludes.return_value = []
        res = schema.schema_info(CONN)
        tables = [x[0] for x in res]
        self.assertIn('explorer_query', tables)

    @patch(patch_location + '_get_includes')
    @patch(patch_location + '_get_excludes')
    def test_table_exclusion_list(self, mocked_excludes, mocked_includes):
        mocked_includes.return_value = None
        mocked_excludes.return_value = ('explorer_',)
        res = schema.schema_info(CONN)
        tables = [x[0] for x in res]
        self.assertNotIn('explorer_query', tables)

    @patch(patch_location + '_get_includes')
    @patch(patch_location + '_get_excludes')
    def test_app_inclusion_list(self, mocked_excludes, mocked_includes):
        mocked_includes.return_value = ('auth_',)
        mocked_excludes.return_value = []
        res = schema.schema_info(CONN)
        tables = [x[0] for x in res]
        self.assertNotIn('explorer_query', tables)
        self.assertIn('auth_user', tables)

    @patch(patch_location + '_get_includes')
    @patch(patch_location + '_get_excludes')
    def test_app_inclusion_list_excluded(self, mocked_excludes, mocked_includes):
        # Inclusion list "wins"
        mocked_includes.return_value = ('explorer_',)
        mocked_excludes.return_value = ('explorer_',)
        res = schema.schema_info(CONN)
        tables = [x[0] for x in res]
        self.assertIn('explorer_query', tables)

    @patch('explorer.schema.do_async')
    def test_builds_async(self, mocked_async_check):
        mocked_async_check.return_value = True
        self.assertIsNone(schema.schema_info(CONN))
        res = schema.schema_info(CONN)
        tables = [x[0] for x in res]
        self.assertIn('explorer_query', tables)
