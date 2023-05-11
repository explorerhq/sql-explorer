from explorer.tasks import execute_query
import six
import logging

from django.http.response import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.views.generic.base import View
from django.views.generic import ListView
from django.views.generic.edit import CreateView, DeleteView
from django.views.decorators.http import require_POST, require_GET
from django.utils.decorators import method_decorator
from django.core.urlresolvers import reverse_lazy
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.db import DatabaseError
from django.db.models import Count
from django.forms import ValidationError
from django.utils.translation import gettext_lazy as _

from explorer.models import Query, QueryLog, QueryChangeLog, MSG_FAILED_BLACKLIST
from explorer import app_settings
from explorer.forms import QueryForm
from explorer.utils import url_get_rows,\
    url_get_query_id,\
    url_get_log_id,\
    schema_info,\
    url_get_params,\
    safe_admin_login_prompt,\
    build_download_response,\
    build_stream_response,\
    user_can_see_query,\
    fmt_sql,\
    allowed_query_pks,\
    url_get_show,\
    compare_sql,\
    check_replication_lag

try:
    from collections import Counter
except:
    from counter import Counter


import re
import json
from functools import wraps

logger = logging.getLogger(__name__)


def view_permission(f):
    @wraps(f)
    def wrap(request, *args, **kwargs):
        if not app_settings.EXPLORER_PERMISSION_VIEW(request.user)\
                and not user_can_see_query(request, kwargs)\
                and not (app_settings.EXPLORER_TOKEN_AUTH_ENABLED()
                         and request.META.get('HTTP_X_API_TOKEN') == app_settings.EXPLORER_TOKEN):
            return safe_admin_login_prompt(request)
        return f(request, *args, **kwargs)
    return wrap


# Users who can only see some queries can still see the list.
# Different than the above because it's not checking for any specific query permissions.
# And token auth does not give you permission to view the list.
def view_permission_list(f):
    @wraps(f)
    def wrap(request, *args, **kwargs):
        if not app_settings.EXPLORER_PERMISSION_VIEW(request.user)\
                and not allowed_query_pks(request.user.id):
            return safe_admin_login_prompt(request)
        return f(request, *args, **kwargs)
    return wrap


def change_permission(f):
    @wraps(f)
    def wrap(request, *args, **kwargs):
        if not app_settings.EXPLORER_PERMISSION_CHANGE(request.user):
            return safe_admin_login_prompt(request)
        return f(request, *args, **kwargs)
    return wrap


class ExplorerContextMixin(object):

    def gen_ctx(self):
        return {'can_view': app_settings.EXPLORER_PERMISSION_VIEW(self.request.user),
                'can_change': app_settings.EXPLORER_PERMISSION_CHANGE(self.request.user)}

    def get_context_data(self, **kwargs):
        ctx = super(ExplorerContextMixin, self).get_context_data(**kwargs)
        ctx.update(self.gen_ctx())
        return ctx

    def render_template(self, template, ctx):
        ctx.update(self.gen_ctx())
        return render_to_response(template, ctx)


@view_permission
@require_GET
def download_query(request, query_id):
    return _csv_response(request, query_id, False, delim=request.GET.get('delim', None))


@view_permission
@require_GET
def view_csv_query(request, query_id):
    return _csv_response(request, query_id, True, delim=request.GET.get('delim', None))


@view_permission
@require_POST
def email_csv_query(request, query_id):
    if request.is_ajax():
        email = request.POST.get('email', None)
        if email:
            execute_query.delay(query_id, email)
            return HttpResponse(content={'message': 'message was sent successfully'})
    return HttpResponse(status=403)


def _csv_response(request, query_id, stream=False, delim=None):
    query = get_object_or_404(Query, pk=query_id)
    query.params = url_get_params(request)
    return build_stream_response(query, delim) if stream else build_download_response(query, delim)


@change_permission
@require_POST
def download_csv_from_sql(request):
    sql = request.POST.get('sql')
    return build_download_response(Query(sql=sql, title="Playground", params=url_get_params(request)))


@change_permission
@require_GET
def schema(request):
    return render_to_response('explorer/schema.html', {'schema': schema_info()})


@require_POST
def format_sql(request):
    sql = request.POST.get('sql', '')
    formatted = fmt_sql(sql)
    return HttpResponse(json.dumps({"formatted": formatted}), content_type="application/json")


class ListQueryView(ExplorerContextMixin, ListView):

    @method_decorator(view_permission_list)
    def dispatch(self, *args, **kwargs):
        return super(ListQueryView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ListQueryView, self).get_context_data(**kwargs)
        context['object_list'] = self._build_queries_and_headers()
        context['recent_queries'] = self.get_queryset().order_by(
            '-last_run_date')[:app_settings.EXPLORER_RECENT_QUERY_COUNT]
        context['tasks_enabled'] = app_settings.ENABLE_TASKS
        return context

    def get_queryset(self):
        if app_settings.EXPLORER_PERMISSION_VIEW(self.request.user):
            qs = Query.objects.prefetch_related('created_by_user').all()
        else:
            qs = Query.objects.prefetch_related('created_by_user').filter(
                pk__in=allowed_query_pks(self.request.user.id))
        return qs.annotate(run_count=Count('querylog'))

    def _build_queries_and_headers(self):
        """
        Build a list of query information and headers (pseudo-folders) for consumption by the template.

        Strategy: Look for queries with titles of the form "something - else" (eg. with a ' - ' in the middle)
                  and split on the ' - ', treating the left side as a "header" (or folder). Interleave the
                  headers into the ListView's object_list as appropriate. Ignore headers that only have one
                  child. The front end uses bootstrap's JS Collapse plugin, which necessitates generating CSS
                  classes to map the header onto the child rows, hence the collapse_target variable.

                  To make the return object homogeneous, convert the object_list models into dictionaries for
                  interleaving with the header "objects". This necessitates special handling of 'created_at'
                  and 'created_by_user' because model_to_dict doesn't include non-editable fields (created_at)
                  and will give the int representation of the user instead of the string representation.

        :return: A list of model dictionaries representing all the query objects, interleaved with header dictionaries.
        """

        dict_list = []
        rendered_headers = []
        pattern = re.compile('[\W_]+')

        headers = Counter([q.title.split(' - ')[0] for q in self.object_list])

        for q in self.object_list:
            model_dict = model_to_dict(q)
            header = q.title.split(' - ')[0]
            collapse_target = pattern.sub('', header)

            if headers[header] > 1 and header not in rendered_headers:
                dict_list.append({'title': header,
                                  'is_header': True,
                                  'collapse_target': collapse_target,
                                  'count': headers[header]})
                rendered_headers.append(header)

            model_dict.update({'is_in_category': headers[header] > 1,
                               'collapse_target': collapse_target,
                               'created_at': q.created_at,
                               'run_count': q.run_count,
                               'created_by_user': six.text_type(q.created_by_user) if q.created_by_user else None})
            dict_list.append(model_dict)
        return dict_list

    model = Query


class ListQueryLogView(ExplorerContextMixin, ListView):

    @method_decorator(view_permission)
    def dispatch(self, *args, **kwargs):
        return super(ListQueryLogView, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        return QueryLog.objects.filter(sql__isnull=False).all()

    context_object_name = "recent_logs"
    model = QueryLog
    paginate_by = 20


class ListQueryChangeLogView(ExplorerContextMixin, ListView):

    @method_decorator(view_permission)
    def dispatch(self, *args, **kwargs):
        return super(ListQueryChangeLogView, self).dispatch(*args, **kwargs)

    def get_queryset(self):
        kwargs = {'old_sql__isnull': False, 'new_sql__isnull': False}
        return QueryChangeLog.objects.filter(**kwargs).all()

    context_object_name = "recent_change_logs"
    model = QueryChangeLog
    paginate_by = 20
    template_name = 'explorer/querychangelog_list.html'


class CreateQueryView(ExplorerContextMixin, CreateView):

    @method_decorator(change_permission)
    def dispatch(self, *args, **kwargs):
        return super(CreateQueryView, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        form.instance.created_by_user = self.request.user
        return super(CreateQueryView, self).form_valid(form)

    form_class = QueryForm
    template_name = 'explorer/query.html'


class DeleteQueryView(ExplorerContextMixin, DeleteView):

    @method_decorator(change_permission)
    def dispatch(self, *args, **kwargs):
        return super(DeleteQueryView, self).dispatch(*args, **kwargs)

    model = Query
    success_url = reverse_lazy("explorer_index")


class PlayQueryView(ExplorerContextMixin, View):

    @method_decorator(change_permission)
    def dispatch(self, *args, **kwargs):
        return super(PlayQueryView, self).dispatch(*args, **kwargs)

    def get(self, request):
        if url_get_query_id(request):
            query = get_object_or_404(Query, pk=url_get_query_id(request))
            return self.render_with_sql(request, query, run_query=False)

        if url_get_log_id(request):
            log = get_object_or_404(QueryLog, pk=url_get_log_id(request))
            query = Query(sql=log.sql, title="Playground")
            return self.render_with_sql(request, query)

        return self.render(request)

    def post(self, request):
        sql = request.POST.get('sql')
        show_results = request.POST.get('show', True)
        query = Query(sql=sql, title="Playground")
        passes_blacklist, failing_words = query.passes_blacklist()
        error = MSG_FAILED_BLACKLIST % ', '.join(
            failing_words) if not passes_blacklist else None
        run_query = not bool(error) if show_results else False
        return self.render_with_sql(request, query, run_query=run_query, error=error)

    def render(self, request):
        return self.render_template('explorer/play.html', RequestContext(request, {'title': 'Playground'}))

    def render_with_sql(self, request, query, run_query=True, error=None):
        return self.render_template('explorer/play.html', query_viewmodel(request, query, title="Playground", run_query=run_query, error=error))


class QueryView(ExplorerContextMixin, View):

    @method_decorator(view_permission)
    def dispatch(self, *args, **kwargs):
        return super(QueryView, self).dispatch(*args, **kwargs)

    def get(self, request, query_id):
        query, form = QueryView.get_instance_and_form(request, query_id)
        query.save()  # updates the modified date
        # if a query is timing out, it can be useful to nav to /query/id/?show=0
        show = url_get_show(request)
        vm = query_viewmodel(request, query, form=form, run_query=show)
        return self.render_template('explorer/query.html', vm)

    def post(self, request, query_id):
        if not app_settings.EXPLORER_PERMISSION_CHANGE(request.user):
            return HttpResponseRedirect(
                reverse_lazy('query_detail', kwargs={'query_id': query_id})
            )
        show = url_get_show(request)
        query, form = QueryView.get_instance_and_form(request, query_id)

        old_sql = query.sql
        form_isvalid = form.is_valid()
        if form_isvalid:
            new_sql = request.POST.get('sql')
            if not compare_sql(old_sql, new_sql):
                change_log = QueryChangeLog(
                    old_sql=old_sql,
                    new_sql=new_sql,
                    query=query,
                    run_by_user=request.user,
                )
                change_log.save()
        success = form_isvalid and form.save()

        try:
            vm = query_viewmodel(
                request,
                query,
                form=form,
                run_query=show,
                message=_("Query saved.") if success else "Query not saved"
            )
        except ValidationError as ve:

            vm = query_viewmodel(
                request,
                query,
                form=form,
                run_query=False,
                
                error=ve.message
            )
        return self.render_template('explorer/query.html', vm)

    @staticmethod
    def get_instance_and_form(request, query_id):
        query = get_object_or_404(Query, pk=query_id)
        query.params = url_get_params(request)
        form = QueryForm(request.POST if len(
            request.POST) else None, instance=query)
        return query, form


def query_viewmodel(request, query, title=None, form=None, message=None, run_query=True, error=None):
    rows = url_get_rows(request)
    res = None
    ql = None
    lag_exists = False
    replication_lag = None
    if run_query:
        try:
            res, ql = query.execute_with_logging(request.user)
            lag_exists, replication_lag = check_replication_lag()
        except DatabaseError as e:
            error = str(e)
    has_valid_results = not error and res and run_query
    ret = RequestContext(request, {
        'tasks_enabled': app_settings.ENABLE_TASKS,
        'params': query.available_params(),
        'title': title,
        'shared': query.shared,
        'query': query,
        'form': form,
        'message': message,
        'error': error,
        'rows': rows,
        'data': res.data[:rows] if has_valid_results else None,
        'headers': res.headers if has_valid_results else None,
        'total_rows': len(res.data) if has_valid_results else None,
        'duration': res.duration if has_valid_results else None,
        'has_stats': len([h for h in res.headers if h.summary]) if has_valid_results else False,
        'dataUrl': reverse_lazy('query_csv', kwargs={'query_id': query.id}) if query.id else '',
        'bucket': app_settings.S3_BUCKET,
        'snapshots': query.snapshots if query.snapshot else [],
        'ql_id': ql.id if ql else None,
        'lag_exists': lag_exists,
        'replication_lag': replication_lag,
    }
    )
    return ret
