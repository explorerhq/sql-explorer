from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.views.generic.base import View
from django.views.generic import ListView
from django.views.generic.edit import CreateView, DeleteView
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST, require_GET
from django.utils.decorators import method_decorator
from django.core.urlresolvers import reverse_lazy

from explorer.actions import generate_report_action
from explorer.models import Query
from explorer.forms import QueryForm
from explorer.utils import url_get_rows, url_get_query_id, schema_info


@staff_member_required
@require_GET
def download_query(request, query_id):
    query = get_object_or_404(Query, pk=query_id)
    fn = generate_report_action()
    return fn(None, None, [query, ])


@staff_member_required
@require_POST
def csv_from_sql(request):
    sql = request.POST.get('sql', None)
    if not sql:
        return PlayQueryView.render(request)
    query = Query(sql=sql)
    fn = generate_report_action()
    return fn(None, None, [query, ])


@staff_member_required
@require_GET
def schema(request):
    return render_to_response('explorer/schema.html', {'schema': schema_info()})


class ListQueryView(ListView):

    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super(ListQueryView, self).dispatch(*args, **kwargs)

    model = Query


class CreateQueryView(CreateView):

    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super(CreateQueryView, self).dispatch(*args, **kwargs)

    form_class = QueryForm
    template_name = 'explorer/query.html'


class DeleteQueryView(DeleteView):

    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super(DeleteQueryView, self).dispatch(*args, **kwargs)

    model = Query
    success_url = reverse_lazy("explorer_index")


class PlayQueryView(View):

    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super(PlayQueryView, self).dispatch(*args, **kwargs)

    def get(self, request):
        if not url_get_query_id(request):
            return PlayQueryView.render(request)
        query = get_object_or_404(Query, pk=url_get_query_id(request))
        return PlayQueryView.render_with_sql(request, query.sql)

    def post(self, request):
        sql = request.POST.get('sql', None)
        if not sql:
            return PlayQueryView.render(request)
        return PlayQueryView.render_with_sql(request, sql)

    @staticmethod
    def render(request):
        c = RequestContext(request, {'title': 'Playground'})
        return render_to_response('explorer/play.html', c)

    @staticmethod
    def render_with_sql(request, sql):
        query = Query(sql=sql)
        headers, data, error = query.headers_and_data()
        c = RequestContext(request, {
            'error': error,
            'title': 'Playground',
            'sql': sql,
            'data': data[:url_get_rows(request)],
            'headers': headers,
            'rows': url_get_rows(request),
            'total_rows': len(data)})
        return render_to_response('explorer/play.html', c)


class QueryView(View):

    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super(QueryView, self).dispatch(*args, **kwargs)

    def get(self, request, query_id):
        query, form = QueryView.get_instance_and_form(request, query_id)
        return QueryView.render(request, query, form, None)

    def post(self, request, query_id):
        query, form = QueryView.get_instance_and_form(request, query_id)
        success = form.save() if form.is_valid() else None
        return QueryView.render(request, query, form, "Query saved." if success else None)

    @staticmethod
    def get_instance_and_form(request, query_id):
        query = get_object_or_404(Query, pk=query_id)
        form = QueryForm(request.POST if len(request.POST) else None, instance=query)
        return query, form

    @staticmethod
    def render(request, query, form, message):
        rows = url_get_rows(request)
        headers, data, error = query.headers_and_data()
        c = RequestContext(request, {
            'error': error,
            'query': query,
            'title': query.title,
            'form': form,
            'message': message,
            'data': data[:rows],
            'headers': headers,
            'rows': rows,
            'total_rows': len(data)}
        )
        return render_to_response('explorer/query.html', c)