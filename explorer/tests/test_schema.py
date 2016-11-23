from django.test import TestCase
from explorer import app_settings
from explorer.utils import get_connection
from explorer.schema import schema_info


class TestSchemaInfo(TestCase):

    def setUp(self):
        self.old_incl = app_settings.EXPLORER_SCHEMA_INCLUDE_TABLE_PREFIXES
        self.old_excl = app_settings.EXPLORER_SCHEMA_EXCLUDE_TABLE_PREFIXES

    def tearDown(self):
        app_settings.EXPLORER_SCHEMA_INCLUDE_TABLE_PREFIXES = self.old_incl
        app_settings.EXPLORER_SCHEMA_EXCLUDE_TABLE_PREFIXES = self.old_excl

    def test_schema_info_returns_valid_data(self):
        res = schema_info(get_connection())
        tables = [x[0] for x in res]
        self.assertIn('explorer_query', tables)

    def test_table_exclusion_list(self):
        app_settings.EXPLORER_SCHEMA_EXCLUDE_TABLE_PREFIXES = ('explorer_',)
        res = schema_info(get_connection())
        tables = [x[0] for x in res]
        self.assertNotIn('explorer_query', tables)

    def test_app_inclusion_list(self):
        app_settings.EXPLORER_SCHEMA_INCLUDE_TABLE_PREFIXES = ('auth_',)
        res = schema_info(get_connection())
        tables = [x[0] for x in res]
        self.assertNotIn('explorer_query', tables)
        self.assertIn('auth_user', tables)

    def test_app_inclusion_list_excluded(self):
        # Inclusion list "wins"
        app_settings.EXPLORER_SCHEMA_INCLUDE_TABLE_PREFIXES = ('explorer_', )
        app_settings.EXPLORER_SCHEMA_EXCLUDE_TABLE_PREFIXES = ('explorer_', )
        res = schema_info(get_connection())
        tables = [x[0] for x in res]
        self.assertIn('explorer_query', tables)

