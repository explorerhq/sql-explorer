from django.test import TestCase
from explorer.utils import get_connection
from explorer import schema


_ = lambda x: x


class TestSchemaInfo(TestCase):

    def tearDown(self):
        schema._get_includes = lambda: None
        schema._get_excludes = lambda: []

    def test_schema_info_returns_valid_data(self):
        schema._get_includes = lambda: None
        schema._get_excludes = lambda: []
        res = schema.schema_info(get_connection())
        tables = [x[0] for x in res]
        self.assertIn('explorer_query', tables)

    def test_table_exclusion_list(self):
        schema._get_includes = lambda: None
        schema._get_excludes = lambda: ('explorer_',)
        res = schema.schema_info(get_connection())
        tables = [x[0] for x in res]
        self.assertNotIn('explorer_query', tables)

    def test_app_inclusion_list(self, ):
        schema._get_includes = lambda: ('auth_',)
        schema._get_excludes = lambda: []
        res = schema.schema_info(get_connection())
        tables = [x[0] for x in res]
        self.assertNotIn('explorer_query', tables)
        self.assertIn('auth_user', tables)

    def test_app_inclusion_list_excluded(self):
        # Inclusion list "wins"
        schema._get_includes = lambda: ('explorer_',)
        schema._get_excludes = lambda: ('explorer_',)
        res = schema.schema_info(get_connection())
        tables = [x[0] for x in res]
        self.assertIn('explorer_query', tables)
