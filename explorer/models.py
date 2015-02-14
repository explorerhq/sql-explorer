from explorer.utils import passes_blacklist, swap_params, execute_query, extract_params, shared_dict_update, get_transforms, transform_row
from django.db import models, DatabaseError
from django.core.urlresolvers import reverse
from django.conf import settings
import app_settings

MSG_FAILED_BLACKLIST = "Query failed the SQL blacklist."


class Query(models.Model):
    title = models.CharField(max_length=255)
    sql = models.TextField()
    description = models.TextField(null=True, blank=True)
    created_by_user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_run_date = models.DateTimeField(auto_now=True)

    def __init__(self, *args, **kwargs):
        self.params = kwargs.get('params')
        kwargs.pop('params', None)
        super(Query, self).__init__(*args, **kwargs)

    class Meta:
        ordering = ['title']
        verbose_name_plural = 'Queries'

    def __unicode__(self):
        return unicode(self.title)

    def passes_blacklist(self):
        return passes_blacklist(self.final_sql())

    def final_sql(self):
        return swap_params(self.sql, self.params)

    def try_execute(self):
        try:
            execute_query(self.final_sql())
        except DatabaseError, e:
            return str(e)

    def headers_and_data(self):
        """
        Retrieve the results from a query.

        :param params: A dictionary of Query param values. These will get merged into the final SQL before execution.
        :return: ([headers], [data], duration in ms, error message)
        """

        if not self.passes_blacklist():
            return QueryResult(headers=[], data=[], duration=None, error=MSG_FAILED_BLACKLIST)
        try:
            return self._execute()
        except (DatabaseError, Warning), e:
            return QueryResult(headers=[], data=[], duration=None, error=str(e))

    def _execute(self):
        cursor, duration = execute_query(self.final_sql())
        headers = [d[0] for d in cursor.description] if cursor.description else ['--']
        transforms = get_transforms(headers, app_settings.EXPLORER_TRANSFORMS)
        return QueryResult(headers=headers,
                           data=[transform_row(transforms, r) for r in cursor.fetchall()],
                           duration=duration,
                           error=None)

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

    def log(self, user):
        log_entry = QueryLog(sql=self.sql, query_id=self.id, run_by_user=user, is_playground=not bool(self.id))
        log_entry.save()


class QueryLog(models.Model):

    sql = models.TextField()
    query = models.ForeignKey(Query, null=True, blank=True, on_delete=models.SET_NULL)
    is_playground = models.BooleanField(default=False)
    run_by_user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)
    run_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-run_at']


class QueryResult(object):

    def __init__(self, headers, data, duration, error):
        self.headers = headers
        self.data = data
        self.duration = duration
        self.error = error