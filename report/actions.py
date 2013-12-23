import tempfile
from zipfile import ZipFile
from datetime import date
from django.http import HttpResponse
from django.core.servers.basehttp import FileWrapper
from collections import defaultdict

_ = lambda x: x


def generate_report_action(description="Generate CSV file from SQL report",):

    def generate_report(modeladmin, request, queryset):
        results = [report for report in queryset if report.passes_blacklist()]
        reports = (len(results) > 0 and _package(results)) or defaultdict(int)
        response = HttpResponse(reports["data"], content_type=reports["content_type"])
        response['Content-Disposition'] = reports["filename"]
        response['Content-Length'] = reports["length"]
        return response
    
    generate_report.short_description = description
    return generate_report


def _package(reports):
    ret = {}
    is_one = len(reports) == 1
    name_root = lambda n: "attachment; filename=%s" % n
    ret["content_type"] = (is_one and 'text/csv') or 'application/zip'
    ret["filename"] = (is_one and name_root('%s.csv' % reports[0].title)) or name_root("Report_%s.zip" % date.today())
    ret["data"] = (is_one and reports[0].csv_report()) or _build_zip(reports)
    ret["length"] = (is_one and len(ret["data"]) or ret["data"].blksize)
    return ret


def _build_zip(reports):
    temp = tempfile.TemporaryFile()
    zip_file = ZipFile(temp, 'w')
    map(lambda r: zip_file.writestr('%s.csv' % r.title, r.csv_report() or "Error!"), reports)
    zip_file.close()
    ret = FileWrapper(temp)
    temp.seek(0)
    return ret


