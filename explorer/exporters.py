import codecs
import csv
import json
import string
import uuid
from datetime import datetime
from io import StringIO, BytesIO

from django.core.serializers.json import DjangoJSONEncoder
from django.utils.module_loading import import_string
from django.utils.text import slugify

from explorer import app_settings


def get_exporter_class(format):
    class_str = dict(getattr(app_settings, 'EXPLORER_DATA_EXPORTERS'))[format]
    return import_string(class_str)


class BaseExporter:

    name = ''
    content_type = ''
    file_extension = ''

    def __init__(self, query):
        self.query = query

    def get_output(self, **kwargs):
        value = self.get_file_output(**kwargs).getvalue()
        return value

    def get_file_output(self, **kwargs):
        res = self.query.execute_query_only()
        return self._get_output(res, **kwargs)

    def _get_output(self, res, **kwargs):
        """
        :param res: QueryResult
        :param kwargs: Optional. Any exporter-specific arguments.
        :return: File-like object
        """
        raise NotImplementedError

    def get_filename(self):
        # build list of valid chars, build filename from title & replace spaces
        valid_chars = f'-_.() {string.ascii_letters}{string.digits}'
        filename = ''.join(c for c in self.query.title if c in valid_chars)
        filename = filename.replace(' ', '_')
        return f'{filename}{self.file_extension}'


class CSVExporter(BaseExporter):

    name = 'CSV'
    content_type = 'text/csv'
    file_extension = '.csv'

    def _get_output(self, res, **kwargs):
        delim = kwargs.get('delim') or app_settings.CSV_DELIMETER
        delim = '\t' if delim == 'tab' else str(delim)
        delim = app_settings.CSV_DELIMETER if len(delim) > 1 else delim
        csv_data = StringIO()
        csv_data.write(codecs.BOM_UTF8.decode('utf-8'))
        writer = csv.writer(csv_data, delimiter=delim)
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
                dict(zip(
                    [str(h) if h is not None else '' for h in res.headers],
                    row
                ))
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

        wb = xlsxwriter.Workbook(output, {'in_memory': True})

        ws = wb.add_worksheet(name=self._format_title())

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
                # xlsxwriter can't handle timezone-aware datetimes or
                # UUIDs, so we help out here and just cast it to a
                # string
                if isinstance(data, datetime) or isinstance(data, uuid.UUID):
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

    def _format_title(self):
        # XLSX writer wont allow sheet names > 31 characters or that
        # contain invalid characters
        # https://github.com/jmcnamara/XlsxWriter/blob/master/xlsxwriter/
        # test/workbook/test_check_sheetname.py
        title = slugify(self.query.title)
        return title[:31]
