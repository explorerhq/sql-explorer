import tempfile
from zipfile import ZipFile
from datetime import date
from wsgiref.util import FileWrapper
from django.http import HttpResponse
from collections import defaultdict
from explorer.utils import csv_report

_ = lambda x: x


def generate_report_action(description="Generate CSV file from SQL query",):

    def generate_report(modeladmin, request, queryset):
        results = [report for report in queryset if report.passes_blacklist()[0]]
        queries = (len(results) > 0 and _package(results)) or defaultdict(int)
        response = HttpResponse(queries["data"], content_type=queries["content_type"])
        response['Content-Disposition'] = queries["filename"]
        response['Content-Length'] = queries["length"]
        return response

    generate_report.short_description = description
    return generate_report


def _package(queries):
    ret = {}
    is_one = len(queries) == 1
    name_root = lambda n: "attachment; filename=%s" % n
    ret["content_type"] = (is_one and 'text/csv') or 'application/zip'
    ret["filename"] = (is_one and name_root('%s.csv' % queries[0].title.replace(',', ''))) or name_root("Report_%s.zip" % date.today())
    ret["data"] = (is_one and csv_report(queries[0]).getvalue()) or _build_zip(queries)
    ret["length"] = (is_one and len(ret["data"]) or ret["data"].blksize)
    return ret


def _build_zip(queries):
    temp = tempfile.TemporaryFile()
    zip_file = ZipFile(temp, 'w')
    for r in queries:
        zip_file.writestr('%s.csv' % r.title, csv_report(r).getvalue() or "Error!")
    zip_file.close()
    ret = FileWrapper(temp)
    temp.seek(0)
    return ret
