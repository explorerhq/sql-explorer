import json
from functools import wraps
import re
import six

from django.core.urlresolvers import reverse_lazy
from django.db import DatabaseError
from django.db.models import Count
from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.http.response import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, render_to_response
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST, require_GET
from django.views.generic import ListView
from django.views.generic.base import View
from django.views.generic.edit import CreateView, DeleteView

from explorer import app_settings
from explorer.exporters import get_exporter_class
from explorer.forms import QueryForm
from explorer.models import Query, QueryLog, MSG_FAILED_BLACKLIST
from explorer.tasks import execute_query
from explorer.utils import url_get_rows,\
    url_get_query_id,\
    url_get_log_id,\
    schema_info,\
    url_get_params,\
    safe_login_prompt,\
    user_can_see_query,\
    fmt_sql,\
    allowed_query_pks,\
    url_get_show

from collections import Counter


def view_permission(f):
    @wraps(f)
    def wrap(request, *args, **kwargs):
        if not app_settings.EXPLORER_PERMISSION_VIEW(request.user)\
                and not user_can_see_query(request, kwargs)\
                and not (app_settings.EXPLORER_TOKEN_AUTH_ENABLED()
                         and request.META.get('HTTP_X_API_TOKEN') == app_settings.EXPLORER_TOKEN):
            return safe_login_prompt(request)
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
            return safe_login_prompt(request)
        return f(request, *args, **kwargs)
    return wrap


def change_permission(f):
    @wraps(f)
    def wrap(request, *args, **kwargs):
        if not app_settings.EXPLORER_PERMISSION_CHANGE(request.user):
            return safe_login_prompt(request)
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
        return render(self.request, template, ctx)


def _export(request, query, download=True):
    format = request.GET.get('format', 'csv')
    exporter_class = get_exporter_class(format)
    query.params = url_get_params(request)
    delim = request.GET.get('delim')
    exporter = exporter_class(query)
    output = exporter.get_output(delim=delim)
    response = HttpResponse(output, content_type=exporter.content_type)
    if download:
        response['Content-Disposition'] = 'attachment; filename="%s"' % (
            exporter.get_filename()
        )
    return response


@view_permission
@require_GET
def download_query(request, query_id):
    query = get_object_or_404(Query, pk=query_id)
    return _export(request, query)


@view_permission
@require_POST
def download_from_sql(request):
    sql = request.POST.get('sql')
    query = Query(sql=sql, title='')
    ql = query.log(request.user)
    query.title = 'Playground - %s' % ql.id
    return _export(request, query)


@view_permission
@require_GET
def stream_query(request, query_id):
    query = get_object_or_404(Query, pk=query_id)
    return _export(request, query, download=False)


@view_permission
@require_POST
def email_csv_query(request, query_id):
    if request.is_ajax():
        email = request.POST.get('email', None)
        if email:
            execute_query.delay(query_id, email)
            return HttpResponse(content={'message': 'message was sent successfully'})
    return HttpResponse(status=403)


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
        context['recent_queries'] = self.get_queryset().order_by('-last_run_date')[:app_settings.EXPLORER_RECENT_QUERY_COUNT]
        context['tasks_enabled'] = app_settings.ENABLE_TASKS
        return context

    def get_queryset(self):
        if app_settings.EXPLORER_PERMISSION_VIEW(self.request.user):
            qs = Query.objects.prefetch_related('created_by_user').all()
        else:
            qs = Query.objects.prefetch_related('created_by_user').filter(pk__in=allowed_query_pks(self.request.user.id))
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
        kwargs = {'sql__isnull': False}
        if url_get_query_id(self.request):
            kwargs['query_id'] = url_get_query_id(self.request)
        return QueryLog.objects.filter(**kwargs).all()

    context_object_name = "recent_logs"
    model = QueryLog
    paginate_by = 20


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
        error = MSG_FAILED_BLACKLIST % ', '.join(failing_words) if not passes_blacklist else None
        run_query = not bool(error) if show_results else False
        return self.render_with_sql(request, query, run_query=run_query, error=error)

    def render(self, request):
        return self.render_template('explorer/play.html', {'title': 'Playground'})

    def render_with_sql(self, request, query, run_query=True, error=None):
        return self.render_template('explorer/play.html', query_viewmodel(request, query, title="Playground"
                                                                          , run_query=run_query, error=error))


class QueryView(ExplorerContextMixin, View):

    @method_decorator(view_permission)
    def dispatch(self, *args, **kwargs):
        return super(QueryView, self).dispatch(*args, **kwargs)

    def get(self, request, query_id):
        query, form = QueryView.get_instance_and_form(request, query_id)
        query.save()  # updates the modified date
        show = url_get_show(request)  # if a query is timing out, it can be useful to nav to /query/id/?show=0
        vm = query_viewmodel(request, query, form=form, run_query=show)
        return self.render_template('explorer/query.html', vm)

    def post(self, request, query_id):
        if not app_settings.EXPLORER_PERMISSION_CHANGE(request.user):
            return HttpResponseRedirect(
                reverse_lazy('query_detail', kwargs={'query_id': query_id})
            )

        query, form = QueryView.get_instance_and_form(request, query_id)
        success = form.is_valid() and form.save()
        vm = query_viewmodel(request, query, form=form, message="Query saved." if success else None)
        return self.render_template('explorer/query.html', vm)

    @staticmethod
    def get_instance_and_form(request, query_id):
        query = get_object_or_404(Query, pk=query_id)
        query.params = url_get_params(request)
        form = QueryForm(request.POST if len(request.POST) else None, instance=query)
        return query, form


def query_viewmodel(request, query, title=None, form=None, message=None, run_query=True, error=None):
    rows = url_get_rows(request)
    res = None
    ql = None
    if run_query:
        try:
            res, ql = query.execute_with_logging(request.user)
        except DatabaseError as e:
            error = str(e)
    has_valid_results = not error and res and run_query
    ret = {
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
        'dataUrl': reverse_lazy('stream_query', kwargs={'query_id': query.id}) if query.id else '',
        'bucket': app_settings.S3_BUCKET,
        'snapshots': query.snapshots if query.snapshot else [],
        'ql_id': ql.id if ql else None
    }
    return ret
