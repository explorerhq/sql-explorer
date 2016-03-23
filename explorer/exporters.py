import json

from django.http import HttpResponse
from django.utils.module_loading import import_string

from . import app_settings
from .utils import csv_report, get_filename_for_title


def get_exporter_class(format):
    class_str = getattr(app_settings, 'EXPLORER_DATA_EXPORTERS')[format]
    return import_string(class_str)


class BaseExporter(object):

    name = ''
    content_type = ''

    def __init__(self, query):
        self.query = query

    def to_response(self):
        raise NotImplementedError


class CSVExporter(BaseExporter):

    name = 'CSV'
    content_type = 'text/csv'

    def to_response(self):
        data = csv_report(self.query, app_settings.CSV_DELIMETER).getvalue()
        response = HttpResponse(data, content_type=self.content_type)
        response['Content-Disposition'] = 'attachment; filename="%s.csv"' % (
            get_filename_for_title(self.query.title)
        )
        response['Content-Length'] = len(data)
        return response


class JSONExporter(BaseExporter):

    name = 'JSON'
    content_type = 'application/json'

    def to_response(self):
        res = self.query.execute_query_only()
        data = []
        for row in res.data:
            data.append(
                dict(zip([str(h) for h in res.headers], row))
            )

        json_data = json.dumps(data)
        response = HttpResponse(json_data, content_type=self.content_type)
        response['Content-Disposition'] = 'attachment; filename="%s.json"' % (
            get_filename_for_title(self.query.title)
        )
        response['Content-Length'] = len(json_data)
        return response


class ExcelExporter(BaseExporter):

    name = 'Excel'
    content_type = 'application/vnd.ms-excel'

    def to_response(self):
        import xlwt
        res = self.query.execute_query_only()

        wb = xlwt.Workbook()
        ws = wb.add_sheet(self.query.title)

        # Write headers
        row = 0
        col = 0
        header_style = xlwt.easyxf('font: bold on; borders: bottom thin')
        for header in res.headers:
            ws.write(row, col, str(header), header_style)
            col += 1

        # Write data
        row = 1
        col = 0
        for data_row in res.data:
            for data in data_row:
                ws.write(row, col, data)
                col += 1
            row += 1
            col = 0

        response = HttpResponse(content_type=self.content_type)
        response['Content-Disposition'] = 'attachment; filename="%s.xls"' % (
            get_filename_for_title(self.query.title)
        )
        wb.save(response)
        return response
