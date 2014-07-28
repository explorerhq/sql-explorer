from explorer.utils import passes_blacklist, write_csv, swap_params, execute_query, execute_and_fetch_query, extract_params, shared_dict_update
from django.db import models, DatabaseError
from django.core.urlresolvers import reverse
from django.conf import settings

MSG_FAILED_BLACKLIST = "Query failed the SQL blacklist."


class Query(models.Model):
    title = models.CharField(max_length=255)
    sql = models.TextField()
    description = models.TextField(null=True, blank=True)
    created_by_user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_run_date = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']
        verbose_name_plural = 'Queries'

    def __unicode__(self):
        return unicode(self.title)

    def passes_blacklist(self, params=None):
        return passes_blacklist(self.final_sql(params=params))

    def final_sql(self, params=None):
        return swap_params(self.sql, params)

    def try_execute(self):
        try:
            execute_query(self.final_sql())
        except DatabaseError, e:
            return str(e)

    def headers_and_data(self, params=None):
        """
        Retrieve the results from a query.

        :param params: A dictionary of Query param values. These will get merged into the final SQL before execution.
        :return: ([headers], [data], duration in ms, error message)
        """

        if not self.passes_blacklist(params):
            return [], [], None, MSG_FAILED_BLACKLIST
        try:
            return execute_and_fetch_query(self.final_sql(params))
        except (DatabaseError, Warning), e:
            return [], [], None, str(e)

    def available_params(self, param_values=None):
        """
        Merge parameter values into a dictionary of available parameters

        :param param_values: A dictionary of Query param values.
        :return: A merged dictionary of parameter names and values. Values of non-existent parameters are removed.
        """

        p = extract_params(self.sql)
        if param_values:
            shared_dict_update(p, param_values)
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
