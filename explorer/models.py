import django
import logging
from time import time
import six

from django.db import models, DatabaseError
if django.VERSION[1] >= 10:
    from django.urls import reverse
else:
    from django.core.urlresolvers import reverse
from django.conf import settings

from . import app_settings
from explorer.utils import (
    passes_blacklist,
    swap_params,
    extract_params,
    shared_dict_update,
    get_connection,
    get_s3_bucket,
    get_params_for_url
)

MSG_FAILED_BLACKLIST = "Query failed the SQL blacklist: %s"


logger = logging.getLogger(__name__)


class Query(models.Model):
    title = models.CharField(max_length=255)
    sql = models.TextField()
    description = models.TextField(null=True, blank=True)
    created_by_user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    last_run_date = models.DateTimeField(auto_now=True)
    snapshot = models.BooleanField(default=False, help_text="Include in snapshot task (if enabled)")

    def __init__(self, *args, **kwargs):
        self.params = kwargs.get('params')
        kwargs.pop('params', None)
        super(Query, self).__init__(*args, **kwargs)

    class Meta:
        ordering = ['title']
        verbose_name_plural = 'Queries'

    def __unicode__(self):
        return six.text_type(self.title)

    def get_run_count(self):
        return self.querylog_set.count()

    def avg_duration(self):
        return self.querylog_set.aggregate(models.Avg('duration'))['duration__avg']

    def passes_blacklist(self):
        return passes_blacklist(self.final_sql())

    def final_sql(self):
        return swap_params(self.sql, self.available_params())

    def execute_query_only(self):
        return QueryResult(self.final_sql())

    def execute_with_logging(self, executing_user):
        ql = self.log(executing_user)
        ret = self.execute()
        ql.duration = ret.duration
        ql.save()
        return ret, ql

    def execute(self):
        ret = self.execute_query_only()
        ret.process()
        return ret

    def available_params(self):
        """
            Merge parameter values into a dictionary of available parameters

        :param param_values: A dictionary of Query param values.
        :return: A merged dictionary of parameter names and values. Values of non-existent parameters are removed.
        """

        p = extract_params(self.sql)
        if self.params:
            shared_dict_update(p, self.params)
        return p

    def get_absolute_url(self):
        return reverse("query_detail", kwargs={'query_id': self.id})

    @property
    def params_for_url(self):
        return get_params_for_url(self)

    def log(self, user=None):
        if user and user.is_anonymous():
            user = None
        ql = QueryLog(sql=self.final_sql(), query_id=self.id, run_by_user=user)
        ql.save()
        return ql

    @property
    def shared(self):
        return self.id in set(sum(app_settings.EXPLORER_GET_USER_QUERY_VIEWS().values(), []))

    @property
    def snapshots(self):
        if app_settings.ENABLE_TASKS:
            b = get_s3_bucket()
            keys = b.list(prefix='query-%s.snap-' % self.id)
            keys_s = sorted(keys, key=lambda k: k.last_modified)
            return [SnapShot(k.generate_url(expires_in=0, query_auth=False),
                             k.last_modified) for k in keys_s]


class SnapShot(object):

    def __init__(self, url, last_modified):
        self.url = url
        self.last_modified = last_modified


class QueryLog(models.Model):

    sql = models.TextField(null=True, blank=True)
    query = models.ForeignKey(Query, null=True, blank=True, on_delete=models.SET_NULL)
    run_by_user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE)
    run_at = models.DateTimeField(auto_now_add=True)
    duration = models.FloatField(blank=True, null=True)  # milliseconds

    @property
    def is_playground(self):
        return self.query_id is None

    class Meta:
        ordering = ['-run_at']


class QueryResult(object):

    def __init__(self, sql):

        self.sql = sql

        cursor, duration = self.execute_query()

        self._description = cursor.description or []
        self._data = [list(r) for r in cursor.fetchall()]
        self.duration = duration

        cursor.close()

        self._headers = self._get_headers()
        self._summary = {}

    @property
    def data(self):
        return self._data or []

    @property
    def headers(self):
        return self._headers or []

    @property
    def header_strings(self):
        return [str(h) for h in self.headers]

    def _get_headers(self):
        return [ColumnHeader(d[0]) for d in self._description] if self._description else [ColumnHeader('--')]

    def _get_numerics(self):
        conn = get_connection()
        if hasattr(conn.Database, "NUMBER"):
            return [ix for ix, c in enumerate(self._description) if hasattr(c, 'type_code') and c.type_code in conn.Database.NUMBER.values]
        elif self.data:
            d = self.data[0]
            return [ix for ix, _ in enumerate(self._description) if not isinstance(d[ix], six.string_types) and six.text_type(d[ix]).isnumeric()]
        return []

    def _get_transforms(self):
        transforms = dict(app_settings.EXPLORER_TRANSFORMS)
        return [(ix, transforms[str(h)]) for ix, h in enumerate(self.headers) if str(h) in transforms.keys()]

    def column(self, ix):
        return [r[ix] for r in self.data]

    def process(self):
        start_time = time()

        self.process_columns()
        self.process_rows()

        logger.info("Explorer Query Processing took %sms." % ((time() - start_time) * 1000))

    def process_columns(self):
        for ix in self._get_numerics():
            self.headers[ix].add_summary(self.column(ix))

    def process_rows(self):
        transforms = self._get_transforms()
        if transforms:
            for r in self.data:
                for ix, t in transforms:
                    r[ix] = t.format(str(r[ix]))

    def execute_query(self):
        conn = get_connection()
        cursor = conn.cursor()
        start_time = time()

        try:
            cursor.execute(self.sql)
        except DatabaseError as e:
            cursor.close()
            raise e

        return cursor, ((time() - start_time) * 1000)


class ColumnHeader(object):

    def __init__(self, title):
        self.title = title.strip()
        self.summary = None

    def add_summary(self, column):
        self.summary = ColumnSummary(self, column)

    def __unicode__(self):
        return self.title

    def __str__(self):
        return self.title


class ColumnStat(object):

    def __init__(self, label, statfn, precision=2, handles_null=False):
        self.label = label
        self.statfn = statfn
        self.precision = precision
        self.handles_null = handles_null

    def __call__(self, coldata):
        self.value = round(float(self.statfn(coldata)), self.precision) if coldata else 0

    def __unicode__(self):
        return self.label


class ColumnSummary(object):

    def __init__(self, header, col):
        self._header = header
        self._stats = [
            ColumnStat("Sum", sum),
            ColumnStat("Avg", lambda x: float(sum(x)) / float(len(x))),
            ColumnStat("Min", min),
            ColumnStat("Max", max),
            ColumnStat("NUL", lambda x: int(sum(map(lambda y: 1 if y is None else 0, x))), 0, True)
        ]
        without_nulls = list(map(lambda x: 0 if x is None else x, col))

        for stat in self._stats:
            stat(col) if stat.handles_null else stat(without_nulls)

    @property
    def stats(self):
        return {c.label: c.value for c in self._stats}

    def __str__(self):
        return str(self._header)
