#encoding=utf8

from django.test import TestCase
from explorer.exporters import CSVExporter, JSONExporter
from explorer.tests.factories import SimpleQueryFactory
from mock import Mock
import json


class TestCsv(TestCase):

    def test_writing_unicode(self):
        res = Mock()
        res.headers = ['a', None]
        res.data = [[1, None], [u"Jenét", '1']]

        res = CSVExporter(query=None)._get_output(res)
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

        res = JSONExporter(query=None)._get_output(res)
        expected = [{'a': 1, '': None}, {'a': 'Jenét', '': '1'}]
        self.assertEqual(res, json.dumps(expected))