from django.test import TestCase
from report.actions import generate_report_action
from report.tests.factories import SimpleReportFactory
from report import app_settings
from report.utils import passes_blacklist, schema_info


class TestSqlBlacklist(TestCase):

    def setUp(self):
        self.orig = app_settings.REPORT_SQL_BLACKLIST

    def tearDown(self):
        app_settings.REPORT_SQL_BLACKLIST = self.orig

    def test_overriding_blacklist(self):
        app_settings.REPORT_SQL_BLACKLIST = []
        r = SimpleReportFactory(sql="SELECT 1+1 AS \"DELETE\";")
        fn = generate_report_action()
        result = fn(None, None, [r, ])
        self.assertEqual(result.content, 'DELETE\r\n2\r\n')

    def test_default_blacklist_prevents_deletes(self):
        r = SimpleReportFactory(sql="SELECT 1+1 AS \"DELETE\";")
        fn = generate_report_action()
        result = fn(None, None, [r, ])
        self.assertEqual(result.content, '0')

    def test_reports_modifying_functions_are_ok(self):
        sql = "SELECT 1+1 AS TWO; drop view foo;"
        self.assertTrue(passes_blacklist(sql))

    def test_reports_deleting_stuff_are_not_ok(self):
        sql = "'distraction'; delete from table; SELECT 1+1 AS TWO; drop view foo;"
        self.assertFalse(passes_blacklist(sql))

    def test_reports_dropping_views_is_ok_and_not_case_sensitive(self):
        sql = "SELECT 1+1 AS TWO; drop ViEw foo;"
        self.assertTrue(passes_blacklist(sql))


class TestSchemaInfo(TestCase):

    def test_schema_info_returns_valid_data(self):
        res = schema_info()
        tables = [a[1] for a in res]
        self.assertIn('report_report', tables)

    def test_app_exclusion_list(self):
        app_settings.REPORT_SCHEMA_EXCLUDE_APPS = ('report',)
        res = schema_info()
        app_settings.REPORT_SCHEMA_EXCLUDE_APPS = ('',)
        tables = [a[1] for a in res]
        self.assertNotIn('report_report', tables)
