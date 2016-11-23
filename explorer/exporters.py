from django.db import DatabaseError
from django.core.serializers.json import DjangoJSONEncoder
import json
import string
import sys
from datetime import datetime
PY3 = sys.version_info[0] == 3
if PY3:
    import csv
else:
    import unicodecsv as csv

from django.utils.module_loading import import_string
from . import app_settings
from six import StringIO, BytesIO


def get_exporter_class(format):
    class_str = dict(getattr(app_settings, 'EXPLORER_DATA_EXPORTERS'))[format]
    return import_string(class_str)


class BaseExporter(object):

    name = ''
    content_type = ''
    file_extension = ''

    def __init__(self, query):
        self.query = query

    def get_output(self, **kwargs):
        value = self.get_file_output(**kwargs).getvalue()
        if PY3:
            return value
        else:
            return str(value)

    def get_file_output(self, **kwargs):
        try:
            res = self.query.execute_query_only()
            return self._get_output(res, **kwargs)
        except DatabaseError as e:
            return StringIO(str(e))

    def _get_output(self, res, **kwargs):
        """
        :param res: QueryResult
        :param kwargs: Optional. Any exporter-specific arguments.
        :return: File-like object
        """
        raise NotImplementedError

    def get_filename(self):
        # build list of valid chars, build filename from title and replace spaces
        valid_chars = '-_.() %s%s' % (string.ascii_letters, string.digits)
        filename = ''.join(c for c in self.query.title if c in valid_chars)
        filename = filename.replace(' ', '_')
        return '{}{}'.format(filename, self.file_extension)


class CSVExporter(BaseExporter):

    name = 'CSV'
    content_type = 'text/csv'
    file_extension = '.csv'

    def _get_output(self, res, **kwargs):
        delim = kwargs.get('delim') or app_settings.CSV_DELIMETER
        delim = '\t' if delim == 'tab' else str(delim)
        delim = app_settings.CSV_DELIMETER if len(delim) > 1 else delim
        csv_data = StringIO()
        if PY3:
            writer = csv.writer(csv_data, delimiter=delim)
        else:
            writer = csv.writer(csv_data, delimiter=delim, encoding='utf-8')
        writer.writerow(res.headers)
        for row in res.data:
            writer.writerow([s for s in row])
        return csv_data


class JSONExporter(BaseExporter):

    name = 'JSON'
    content_type = 'application/json'
    file_extension = '.json'

    def _get_output(self, res, **kwargs):
        data = []
        for row in res.data:
            data.append(
                dict(zip([str(h) if h is not None else '' for h in res.headers], row))
            )

        json_data = json.dumps(data, cls=DjangoJSONEncoder)
        return StringIO(json_data)


class ExcelExporter(BaseExporter):

    name = 'Excel'
    content_type = 'application/vnd.ms-excel'
    file_extension = '.xlsx'

    def _get_output(self, res, **kwargs):
        import xlsxwriter
        output = BytesIO()

        wb = xlsxwriter.Workbook(output)

        # XLSX writer wont allow sheet names > 31 characters
        # https://github.com/jmcnamara/XlsxWriter/blob/master/xlsxwriter/test/workbook/test_check_sheetname.py
        title = self.query.title[:31]

        ws = wb.add_worksheet(name=title)

        # Write headers
        row = 0
        col = 0
        header_style = wb.add_format({'bold': True})
        for header in res.header_strings:
            ws.write(row, col, header, header_style)
            col += 1

        # Write data
        row = 1
        col = 0
        for data_row in res.data:
            for data in data_row:
                # xlsxwriter can't handle timezone-aware datetimes, so we help out here and just cast it to a string
                if isinstance(data, datetime):
                    data = str(data)
                # JSON and Array fields
                if isinstance(data, dict) or isinstance(data, list):
                    data = json.dumps(data)
                ws.write(row, col, data)
                col += 1
            row += 1
            col = 0

        wb.close()
        return output


class PdfExporter(BaseExporter):

    name = 'PDF'
    content_type = 'application/pdf'
    file_extension = '.pdf'

    def _get_output(self, res, **kwargs):
        from django_xhtml2pdf.utils import generate_pdf
        output = BytesIO()
        
        ctx = {
            'headers': res.header_strings,
            'data': res.data,
        }
        result = generate_pdf('explorer/pdf_template.html', file_object=output, context=ctx)
        return output

