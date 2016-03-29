import io
from django.test import TestCase
from explorer.actions import generate_report_action
from explorer.tests.factories import SimpleQueryFactory
from zipfile import ZipFile


class TestSqlQueryActions(TestCase):

    def test_single_query_is_csv_file(self):
        expected_csv = b'two\r\n2\r\n'

        r = SimpleQueryFactory()
        fn = generate_report_action()
        result = fn(None, None, [r, ])
        self.assertEqual(result.content.lower(), expected_csv)

    def test_multiple_queries_are_zip_file(self):

        expected_csv = 'two\r\n2\r\n'

        q = SimpleQueryFactory()
        q2 = SimpleQueryFactory()
        fn = generate_report_action()

        res = fn(None, None, [q,q2])
        z = ZipFile(io.BytesIO(res.content))
        got_csv = z.read(z.namelist()[0])

        self.assertEqual(len(z.namelist()), 2)
        self.assertEqual(z.namelist()[0], '%s.csv' % q.title)
        self.assertEqual(got_csv.lower().decode('utf-8'), expected_csv)

    # if commas are not removed from the filename, then Chrome throws "duplicate headers received from server"
    def test_packaging_removes_commas_from_file_name(self):

        expected = 'attachment; filename=query for x y.csv'
        q = SimpleQueryFactory(title='query for x, y')
        fn = generate_report_action()
        res = fn(None, None, [q])
        self.assertEqual(res['Content-Disposition'], expected)
