from django.http.response import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.views.generic.base import View
from django.views.generic import ListView
from django.views.generic.edit import CreateView, DeleteView
from django.views.decorators.http import require_POST, require_GET
from django.utils.decorators import method_decorator
from django.core.urlresolvers import reverse_lazy

from explorer.actions import generate_report_action
from explorer.models import Query
from explorer.app_settings import EXPLORER_PERMISSION_VIEW, EXPLORER_PERMISSION_CHANGE
from explorer.forms import QueryForm
from explorer.utils import url_get_rows, url_get_query_id, schema_info, url_get_params, safe_admin_login_prompt


def view_permission(f):
    def wrap(request, *args, **kwargs):
        if not EXPLORER_PERMISSION_VIEW(request.user):
            return safe_admin_login_prompt(request)
        return f(request, *args, **kwargs)
    return wrap


def change_permission(f):
    def wrap(request, *args, **kwargs):
        if not EXPLORER_PERMISSION_CHANGE(request.user):
            return safe_admin_login_prompt(request)
        return f(request, *args, **kwargs)
    return wrap


class ExplorerContextMixin(object):

    def gen_ctx(self):
        return {'can_view': EXPLORER_PERMISSION_VIEW(self.request.user),
                'can_change': EXPLORER_PERMISSION_CHANGE(self.request.user)}

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
    query = get_object_or_404(Query, pk=query_id)
    query.params = url_get_params(request)
    fn = generate_report_action()
    return fn(None, None, [query, ])


@change_permission
@require_POST
def csv_from_sql(request):
    sql = request.POST.get('sql', None)
    if not sql:
        return PlayQueryView.render(request)
    query = Query(sql=sql)
    query.params = url_get_params(request)
    fn = generate_report_action()
    return fn(None, None, [query, ])


@change_permission
@require_GET
def schema(request):
    return render_to_response('explorer/schema.html', {'schema': schema_info()})


class ListQueryView(ExplorerContextMixin, ListView):

    @method_decorator(view_permission)
    def dispatch(self, *args, **kwargs):
        return super(ListQueryView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ListQueryView, self).get_context_data(**kwargs)
        context['title'] = 'All Queries'
        return context

    model = Query


class CreateQueryView(ExplorerContextMixin, CreateView):

    @method_decorator(change_permission)
    def dispatch(self, *args, **kwargs):
        return super(CreateQueryView, self).dispatch(*args, **kwargs)

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
        if not url_get_query_id(request):
            return self.render(request)
        query = get_object_or_404(Query, pk=url_get_query_id(request))
        query.params = url_get_params(request)
        return self.render_with_sql(request, query)

    def post(self, request):
        sql = request.POST.get('sql', None)
        if not sql:
            return PlayQueryView.render(request)
        query = Query(sql=sql, title="Playground")
        query.params = url_get_params(request)
        return self.render_with_sql(request, query)

    def render(self, request):
        c = RequestContext(request, {'title': 'Playground'})
        return self.render_template('explorer/play.html', c)

    def render_with_sql(self, request, query):
        return self.render_template('explorer/play.html', query_viewmodel(request, query, title="Playground"))


class QueryView(ExplorerContextMixin, View):

    @method_decorator(view_permission)
    def dispatch(self, *args, **kwargs):
        return super(QueryView, self).dispatch(*args, **kwargs)

    def get(self, request, query_id):
        query, form = QueryView.get_instance_and_form(request, query_id)
        vm = query_viewmodel(request, query, form=form, message=None)
        return self.render_template('explorer/query.html', vm)

    def post(self, request, query_id):
        if not EXPLORER_PERMISSION_CHANGE(request.user):
            return HttpResponseRedirect(
                reverse_lazy('query_detail', kwargs={'query_id': query_id})
            )

        query, form = QueryView.get_instance_and_form(request, query_id)
        success = form.save() if form.is_valid() else None
        vm = query_viewmodel(request, query, form=form, message="Query saved." if success else None)
        return self.render_template('explorer/query.html', vm)

    @staticmethod
    def get_instance_and_form(request, query_id):
        query = get_object_or_404(Query, pk=query_id)
        query.params = url_get_params(request)
        form = QueryForm(request.POST if len(request.POST) else None, instance=query)
        return query, form


def query_viewmodel(request, query, title=None, form=None, message=None):
    rows = url_get_rows(request)
    headers, data, duration, error = query.headers_and_data()
    return RequestContext(request, {
            'error': error,
            'params': query.available_params(),
            'title': title,
            'query': query,
            'form': form,
            'message': message,
            'data': data[:rows],
            'headers': headers,
            'duration': duration,
            'rows': rows,
            'total_rows': len(data)})