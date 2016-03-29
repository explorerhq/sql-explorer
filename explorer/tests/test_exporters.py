#encoding=utf8

from django.test import TestCase
from django.core.serializers.json import DjangoJSONEncoder
from explorer.exporters import CSVExporter, JSONExporter, ExcelExporter
from explorer.tests.factories import SimpleQueryFactory
from mock import Mock
import json
from datetime import datetime


class TestCsv(TestCase):

    def test_writing_unicode(self):
        res = Mock()
        res.headers = ['a', None]
        res.data = [[1, None], [u"Jenét", '1']]

        res = CSVExporter(query=None)._get_output(res).getvalue()
        self.assertEqual(res, 'a,\r\n1,\r\nJenét,1\r\n')

    def test_custom_delimiter(self):
        q = SimpleQueryFactory(sql='select 1, 2')
        exporter = CSVExporter(query=q)
        res = exporter.get_output(delim='|')
        self.assertEqual(res, '1|2\r\n1|2\r\n')


class TestJson(TestCase):

    def test_writing_json(self):
        res = Mock()
        res.headers = ['a', None]
        res.data = [[1, None], [u"Jenét", '1']]

        res = JSONExporter(query=None)._get_output(res).getvalue()
        expected = [{'a': 1, '': None}, {'a': 'Jenét', '': '1'}]
        self.assertEqual(res, json.dumps(expected))

    def test_writing_datetimes(self):
        res = Mock()
        res.headers = ['a', 'b']
        res.data = [[1, datetime.now()]]

        res = JSONExporter(query=None)._get_output(res).getvalue()
        expected = [{'a': 1, 'b': datetime.now()}]
        self.assertEqual(res, json.dumps(expected, cls=DjangoJSONEncoder))


class TestExcel(TestCase):

    def test_writing_excel(self):
        res = Mock()
        res.headers = ['a', None]
        res.data = [[1, None], [u"Jenét", '1']]

        res = ExcelExporter(query=None)._get_output(res).getvalue()

        expected = None

        self.assertEqual(res, json.dumps(expected))