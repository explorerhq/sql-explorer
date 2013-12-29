from django.test import TestCase
from report.actions import generate_report_action
from report.tests.factories import SimpleReportFactory
from report import app_settings
import StringIO
from zipfile import ZipFile


class testSqlReportActions(TestCase):

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