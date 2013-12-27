from django.db import models
from report.utils import passes_blacklist
from report import app_settings
import logging
import csv
import cStringIO
from django.db import connection, DatabaseError

logger = logging.getLogger(app_settings.REPORT_LOGGER_NAME)


class Report(models.Model):
    title = models.CharField(max_length=255)
    sql = models.TextField()
    description = models.TextField(null=True, blank=True)
    created_by = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        ordering = ['title']
    
    def __unicode__(self):
        return unicode(self.title)

    def passes_blacklist(self):
        return passes_blacklist(self.sql)

    def csv_report(self):
        csv_report = cStringIO.StringIO()
        writer = csv.writer(csv_report)
        headers, data, error = self.headers_and_data()
        if error: return error
        writer.writerow(headers)
        map(lambda row: writer.writerow(row), data)
        return csv_report.getvalue()

    def headers_and_data(self):
        cursor = connection.cursor()
        try:
            cursor.execute(self.sql)
        except DatabaseError, e:
            logger.exception("Error while running report %s (ID: %s): %s" % (self.title, self.id, e))
            return [], [], e.message
        headers = [d[0] for d in cursor.description]
        data = [[x.encode('utf-8') if type(x) is unicode else x for x in list(r)] for r in cursor.fetchall()]
        return headers, data, None

    def get_absolute_url(self):
        from django.core.urlresolvers import reverse
        return reverse("report_detail", kwargs={'report_id': self.id})