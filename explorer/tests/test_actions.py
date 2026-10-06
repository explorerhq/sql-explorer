import io
from unittest.mock import patch
from zipfile import ZipFile

from django.test import TestCase

from explorer.actions import generate_report_action
from explorer.tests.factories import SimpleQueryFactory


class TestSqlQueryActions(TestCase):

    def test_single_query_is_csv_file(self):
        expected_csv = "two\r\n2\r\n"

        r = SimpleQueryFactory()
        fn = generate_report_action()
        result = fn(None, None, [r, ])
        self.assertEqual(result.content.lower().decode("utf-8-sig"), expected_csv)
        self.assertEqual(int(result["Content-Length"]), len(result.content))

    @patch("explorer.actions.CSVExporter.get_output")
    def test_single_query_with_unicode_has_byte_content_length(self, get_output):
        get_output.return_value = "name\r\nЗавершен\r\n"

        result = generate_report_action()(None, None, [SimpleQueryFactory()])

        self.assertEqual(int(result["Content-Length"]), len(result.content))
        self.assertGreater(len(result.content), len(get_output.return_value))

    def test_multiple_queries_are_zip_file(self):

        expected_csv = "two\r\n2\r\n"

        q = SimpleQueryFactory()
        q2 = SimpleQueryFactory()
        fn = generate_report_action()

        res = fn(None, None, [q, q2])
        z = ZipFile(io.BytesIO(res.content))
        got_csv = z.read(z.namelist()[0])

        self.assertEqual(len(z.namelist()), 2)
        self.assertEqual(z.namelist()[0], f"{q.title}.csv")
        self.assertEqual(got_csv.lower().decode("utf-8-sig"), expected_csv)
        self.assertEqual(int(res["Content-Length"]), len(res.content))

    # if commas are not removed from the filename, then Chrome throws
    # "duplicate headers received from server"
    def test_packaging_removes_commas_from_file_name(self):

        expected = "attachment; filename=query for x y.csv"
        q = SimpleQueryFactory(title="query for x, y")
        fn = generate_report_action()
        res = fn(None, None, [q])
        self.assertEqual(res["Content-Disposition"], expected)
