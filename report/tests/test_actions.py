from django.test import TestCase
from report.actions import _get_report, generate_report_action, _is_read_only
from report.tests.factories import SimpleReportFactory
import StringIO
from zipfile import ZipFile


class test_sql_reports(TestCase):

    def test_simple_report_runs(self):

        expected_csv = 'two\r\n2\r\n'

        r = SimpleReportFactory()
        result = _get_report(r)

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

    def test_reports_are_read_only(self):
        r = SimpleReportFactory(sql="delete * from table;")
        fn = generate_report_action()
        result = fn(None, None, [r, ])
        self.assertEqual(result.content, '0')

    def test_reports_modifying_functions_are_ok(self):
        sql = "SELECT 1+1 AS TWO; drop view foo;"
        self.assertTrue(_is_read_only(sql))

    def test_reports_deleting_stuff_are_not_ok(self):
        sql = "'distraction'; delete * from table; SELECT 1+1 AS TWO; drop view foo;"
        self.assertFalse(_is_read_only(sql))

    def test_reports_dropping_views_is_ok_and_not_case_sensitive(self):
        sql = "SELECT 1+1 AS TWO; drop ViEw foo;"
        self.assertTrue(_is_read_only(sql))