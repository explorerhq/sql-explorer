from django.test import TestCase
from explorer.actions import generate_report_action
from explorer.tests.factories import SimpleQueryFactory
from explorer import app_settings
from explorer.utils import passes_blacklist, schema_info, param, swap_params, extract_params, shared_dict_update, EXPLORER_PARAM_TOKEN, execute_query


class TestSqlBlacklist(TestCase):

    def setUp(self):
        self.orig = app_settings.EXPLORER_SQL_BLACKLIST

    def tearDown(self):
        app_settings.EXPLORER_SQL_BLACKLIST = self.orig

    def test_overriding_blacklist(self):
        app_settings.EXPLORER_SQL_BLACKLIST = []
        r = SimpleQueryFactory(sql="SELECT 1+1 AS \"DELETE\";")
        fn = generate_report_action()
        result = fn(None, None, [r, ])
        self.assertEqual(result.content, 'DELETE\r\n2\r\n')

    def test_default_blacklist_prevents_deletes(self):
        r = SimpleQueryFactory(sql="SELECT 1+1 AS \"DELETE\";")
        fn = generate_report_action()
        result = fn(None, None, [r, ])
        self.assertEqual(result.content, '0')

    def test_queries_modifying_functions_are_ok(self):
        sql = "SELECT 1+1 AS TWO; drop view foo;"
        self.assertTrue(passes_blacklist(sql))

    def test_queries_deleting_stuff_are_not_ok(self):
        sql = "'distraction'; delete from table; SELECT 1+1 AS TWO; drop view foo;"
        self.assertFalse(passes_blacklist(sql))

    def test_queries_dropping_views_is_ok_and_not_case_sensitive(self):
        sql = "SELECT 1+1 AS TWO; drop ViEw foo;"
        self.assertTrue(passes_blacklist(sql))


class TestSchemaInfo(TestCase):

    def test_schema_info_returns_valid_data(self):
        res = schema_info()
        tables = [a[1] for a in res]
        self.assertIn('explorer_query', tables)

    def test_app_exclusion_list(self):
        app_settings.EXPLORER_SCHEMA_EXCLUDE_APPS = ('explorer',)
        res = schema_info()
        app_settings.EXPLORER_SCHEMA_EXCLUDE_APPS = ('',)
        tables = [a[1] for a in res]
        self.assertNotIn('explorer_query', tables)


class TestParams(TestCase):

    def test_swappable_params_are_built_correctly(self):
        expected = EXPLORER_PARAM_TOKEN + 'foo' + EXPLORER_PARAM_TOKEN
        self.assertEqual(expected, param('foo'))

    def test_params_get_swapped(self):
        sql = 'please swap $$this$$ and $$that$$'
        expected = 'please swap here and there'
        params = {'this': 'here', 'that': 'there'}
        got = swap_params(sql, params)
        self.assertEqual(got, expected)

    def test_empty_params_does_nothing(self):
        sql = 'please swap $$this$$ and $$that$$'
        params = None
        got = swap_params(sql, params)
        self.assertEqual(got, sql)

    def test_non_string_param_gets_swapper(self):
        sql = 'please swap $$this$$'
        expected = 'please swap 1'
        params = {'this': 1}
        got = swap_params(sql, params)
        self.assertEqual(got, expected)

    def test_extracting_params(self):
        sql = 'please swap $$this$$'
        expected = {'this': ''}
        self.assertEqual(extract_params(sql), expected)

    def test_shared_dict_update(self):
        source = {'foo': 1, 'bar': 2}
        target = {'bar': None}  # ha ha!
        self.assertEqual({'bar': 2}, shared_dict_update(target, source))

    def test_execution_time_measure(self):
        for i in range(1000):
            SimpleQueryFactory()
        c, t = execute_query('select 1;')
        c2, t2 = execute_query('select * from explorer_query q1 inner join explorer_query q2 on q1.id=q2.id inner join explorer_query q3 on q1.id=q3.id order by id desc')
        self.assertGreater(t2, t)
