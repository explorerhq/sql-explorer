import tempfile
import csv
import cStringIO
from zipfile import ZipFile
from datetime import date
from django.http import HttpResponse
from django.db import connection, DatabaseError
from django.core.servers.basehttp import FileWrapper
import logging
from collections import defaultdict
import functools

logger = logging.getLogger('django')

_ = lambda x: x

SQL_WRITE_BLACKLIST = ('ALTER', 'RENAME ', 'DROP', 'TRUNCATE', 'INSERT INTO', 'UPDATE', 'REPLACE', 'DELETE')
SQL_WHITELIST = ('DROP FUNCTION', 'REPLACE FUNCTION', 'DROP VIEW', 'REPLACE VIEW', 'CREATED', 'DELETED')  # no other way to manage these in django


def generate_report_action(description="Generate CSV file from SQL report",):

    def generate_report(modeladmin, request, queryset):
        results = [report for report in queryset if _is_read_only(report.sql)]
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
    ret["data"] = (is_one and _get_report(reports[0])) or _build_zip(reports)
    ret["length"] = (is_one and len(ret["data"]) or ret["data"].blksize)
    return ret


def _build_zip(reports):
    temp = tempfile.TemporaryFile()
    zip_file = ZipFile(temp, 'w')
    for r in reports:
        zip_file.writestr('%s.csv' % r.title, _get_report(r) or "Error!")
    zip_file.close()
    ret = FileWrapper(temp)
    temp.seek(0)
    return ret


def _get_report(report):
    cursor = connection.cursor()
    csv_report = cStringIO.StringIO()
    writer = csv.writer(csv_report)
    sql = report.sql

    try:
        cursor.execute(sql)
    except DatabaseError:
        logger.exception("Error while running report %s" % report.title)
        return None

    headers = [d[0] for d in cursor.description]
    writer.writerow(headers)
    for r in cursor.fetchall():
        row = [x.encode('utf-8') if type(x) is unicode else x for x in list(r)]
        writer.writerow(row)

    return csv_report.getvalue()


def _is_read_only(sql):
    cleansed = functools.reduce(lambda sql, term: sql.upper().replace(term, ""), SQL_WHITELIST, sql)
    return not any(write_word in cleansed.upper() for write_word in SQL_WRITE_BLACKLIST)