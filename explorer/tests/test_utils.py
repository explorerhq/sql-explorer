#encoding=utf8

from django.test import TestCase
from explorer.actions import generate_report_action
from explorer.tests.factories import SimpleQueryFactory
from explorer import app_settings
from explorer.utils import passes_blacklist, schema_info, param, swap_params, extract_params,\
    shared_dict_update, EXPLORER_PARAM_TOKEN, write_csv, get_params_from_request
from mock import Mock


class TestSqlBlacklist(TestCase):

    def setUp(self):
        self.orig = app_settings.EXPLORER_SQL_BLACKLIST
        self.orig_wl = app_settings.EXPLORER_SQL_WHITELIST

    def tearDown(self):
        app_settings.EXPLORER_SQL_BLACKLIST = self.orig
        app_settings.EXPLORER_SQL_WHITELIST = self.orig_wl

    def test_overriding_blacklist(self):
        app_settings.EXPLORER_SQL_BLACKLIST = []
        r = SimpleQueryFactory(sql="SELECT 1+1 AS \"DELETE\";")
        fn = generate_report_action()
        result = fn(None, None, [r, ])
        self.assertEqual(result.content, b'DELETE\r\n2\r\n')

    def test_default_blacklist_prevents_deletes(self):
        r = SimpleQueryFactory(sql="SELECT 1+1 AS \"DELETE\";")
        fn = generate_report_action()
        result = fn(None, None, [r, ])
        self.assertEqual(result.content.decode('utf-8'), '0')

    def test_queries_deleting_stuff_are_not_ok(self):
        sql = "'distraction'; deLeTe from table; SELECT 1+1 AS TWO; drop view foo;"
        passes, words = passes_blacklist(sql)
        self.assertFalse(passes)
        self.assertTrue(len(words), 2)
        self.assertEqual(words[0], 'DROP')
        self.assertEqual(words[1], 'DELETE')

    def test_queries_dropping_views_is_not_ok_and_not_case_sensitive(self):
        sql = "SELECT 1+1 AS TWO; drop ViEw foo;"
        self.assertFalse(passes_blacklist(sql)[0])

    def test_sql_whitelist_ok(self):
        app_settings.EXPLORER_SQL_WHITELIST = ['dropper']
        sql = "SELECT 1+1 AS TWO; dropper ViEw foo;"
        self.assertTrue(passes_blacklist(sql)[0])


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

    def _assertSwap(self, tuple):
        self.assertEqual(extract_params(tuple[0]), tuple[1])

    def test_extracting_params(self):
        tests = [
            ('please swap $$this0$$',                {'this0': ''}),
            ('please swap $$this6$$ $$this6:that$$', {'this6': 'that'}),
            ('please swap $$this_7:foo, bar$$',      {'this_7': 'foo, bar'}),
            ('please swap $$this8:$$',               {}),
            ('do nothing with $$this1 $$',           {}),
            ('do nothing with $$this2 :$$',          {}),
            ('do something with $$this3: $$',        {'this3': ' '}),
            ('do nothing with $$this4: ',            {}),
            ('do nothing with $$this5$that$$',       {}),
        ]
        for s in tests:
            self._assertSwap(s)

    def test_shared_dict_update(self):
        source = {'foo': 1, 'bar': 2}
        target = {'bar': None}  # ha ha!
        self.assertEqual({'bar': 2}, shared_dict_update(target, source))

    def test_get_params_from_url(self):
        r = Mock()
        r.GET = {'params': 'foo:bar|qux:mux'}
        res = get_params_from_request(r)
        self.assertEqual(res['foo'], 'bar')
        self.assertEqual(res['qux'], 'mux')


class TestCsv(TestCase):

    def test_writing_unicode(self):
        headers = ['a', None]
        data = [[1, None], [u"Jenét", '1']]
        res = write_csv(headers, data).getvalue()
        self.assertEqual(res, 'a,\r\n1,\r\nJenét,1\r\n')