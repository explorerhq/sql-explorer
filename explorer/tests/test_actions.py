from django.test import TestCase
from explorer.actions import generate_report_action
from explorer.tests.factories import SimpleQueryFactory
import StringIO
from zipfile import ZipFile


class testSqlQueryActions(TestCase):

    def test_simple_query_runs(self):

        expected_csv = 'two\r\n2\r\n'

        r = SimpleQueryFactory()
        result = r.csv_report()

        self.assertIsNotNone(result, "Query '%s' returned None." % r.title)
        self.assertEqual(result.lower(), expected_csv)

    def test_single_query_is_csv_file(self):
        expected_csv = 'two\r\n2\r\n'

        r = SimpleQueryFactory()
        fn = generate_report_action()
        result = fn(None, None, [r, ])
        self.assertEqual(result.content.lower(), expected_csv)

    def test_multiple_queries_are_zip_file(self):

        expected_csv = 'two\r\n2\r\n'

        q = SimpleQueryFactory()
        q2 = SimpleQueryFactory()
        fn = generate_report_action()
        res = fn(None, None, [q, q2])
        z = ZipFile(StringIO.StringIO(res.content))
        got_csv = z.read(z.namelist()[0])

        self.assertEqual(len(z.namelist()), 2)
        self.assertEqual(z.namelist()[0], '%s.csv' % q.title)
        self.assertEqual(got_csv.lower(), expected_csv)