#encoding=utf8

from django.test import TestCase
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone
from explorer.exporters import CSVExporter, JSONExporter, ExcelExporter
from explorer.tests.factories import SimpleQueryFactory
from explorer.models import QueryResult
import json
from datetime import date, datetime
from six import b


class TestCsv(TestCase):

    def test_writing_unicode(self):
        res = QueryResult(SimpleQueryFactory(sql='select 1 as "a", 2 as ""').sql)
        res.execute_query()
        res.process()
        res._data = [[1, None], [u"Jenét", '1']]

        res = CSVExporter(query=None)._get_output(res).getvalue()
        self.assertEqual(res, 'a,\r\n1,\r\nJenét,1\r\n')

    def test_custom_delimiter(self):
        q = SimpleQueryFactory(sql='select 1, 2')
        exporter = CSVExporter(query=q)
        res = exporter.get_output(delim='|')
        self.assertEqual(res, '1|2\r\n1|2\r\n')


class TestJson(TestCase):

    def test_writing_json(self):
        res = QueryResult(SimpleQueryFactory(sql='select 1 as "a", 2 as ""').sql)
        res.execute_query()
        res.process()
        res._data = [[1, None], [u"Jenét", '1']]

        res = JSONExporter(query=None)._get_output(res).getvalue()
        expected = [{'a': 1, '': None}, {'a': 'Jenét', '': '1'}]
        self.assertEqual(res, json.dumps(expected))

    def test_writing_datetimes(self):
        res = QueryResult(SimpleQueryFactory(sql='select 1 as "a", 2 as "b"').sql)
        res.execute_query()
        res.process()
        res._data = [[1, date.today()]]

        res = JSONExporter(query=None)._get_output(res).getvalue()
        expected = [{'a': 1, 'b': date.today()}]
        self.assertEqual(res, json.dumps(expected, cls=DjangoJSONEncoder))


class TestExcel(TestCase):

    def test_writing_excel(self):
        """ This is a pretty crap test. It at least exercises the code.
            If anyone wants to go through the brain damage of actually building
            an 'expected' xlsx output and comparing it
            (see https://github.com/jmcnamara/XlsxWriter/blob/master/xlsxwriter/test/helperfunctions.py for reference)
            , by all means submit a pull request!
        """
        res = QueryResult(SimpleQueryFactory(sql='select 1 as "a", 2 as ""',
                                             title='this title is longer than 32 characters').sql)
        res.execute_query()
        res.process()

        d = datetime.now()
        d = timezone.make_aware(d, timezone.get_current_timezone())

        res._data = [[1, None], [u"Jenét", d]]

        res = ExcelExporter(query=SimpleQueryFactory())._get_output(res).getvalue()

        expected = b('PK')

        self.assertEqual(res[:2], expected)