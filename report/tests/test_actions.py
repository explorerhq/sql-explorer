from django.test import TestCase
from report.actions import generate_report_action
from report.tests.factories import SimpleReportFactory
from report import app_settings
import StringIO
from zipfile import ZipFile
from report.utils import passes_blacklist


class test_sql_reports(TestCase):

    def test_simple_report_runs(self):

        expected_csv = 'two\r\n2\r\n'

        r = SimpleReportFactory()
        result = r.csv_report()

        self.assertIsNotNone(result, "Report '%s' returned None." % r.title)
        self.assertEqual(result.lower(), expected_csv)

    def test_single_report_is_csv_file(self):
        expected_csv = 'two\r\n2\r\n'

        r = SimpleReportFactory()
        fn = generate_report_action()
        result = fn(None, None, [r, ])
        self.assertEqual(result.content.lower(), expected_csv)

    def test_multiple_reports_are_zip_file(self):

        expected_csv = 'two\r\n2\r\n'

        r = SimpleReportFactory()
        r2 = SimpleReportFactory()
        fn = generate_report_action()
        res = fn(None, None, [r, r2])
        z = ZipFile(StringIO.StringIO(res.content))
        got_csv = z.read(z.namelist()[0])

        self.assertEqual(len(z.namelist()), 2)
        self.assertEqual(z.namelist()[0], '%s.csv' % r.title)
        self.assertEqual(got_csv.lower(), expected_csv)


class test_sql_blacklist(TestCase):

    def test_overriding_blacklist(self):
        tmp = app_settings.SQL_BLACKLIST
        app_settings.SQL_BLACKLIST = []
        r = SimpleReportFactory(sql="SELECT 1+1 AS \"DELETE\";")
        fn = generate_report_action()
        result = fn(None, None, [r, ])
        app_settings.SQL_BLACKLIST = tmp
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