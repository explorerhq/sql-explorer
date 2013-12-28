from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.views.generic.base import View
from django.views.generic.edit import CreateView, DeleteView
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.core.urlresolvers import reverse_lazy

from report.actions import generate_report_action
from report.models import Report
from report.forms import ReportForm
from report.utils import url_get_rows, url_get_report_id
from report.schemainfo import schemainfo

@staff_member_required
def download_report(request, report_id):
    report = get_object_or_404(Report, pk=report_id)
    fn = generate_report_action()
    return fn(None, None, [report, ])


def schema(request):
    return render_to_response('report/schema.html', {'schema': schemainfo()})


class CreateReportView(CreateView):

    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super(CreateReportView, self).dispatch(*args, **kwargs)

    form_class = ReportForm
    template_name = 'report/report.html'


class DeleteReportView(DeleteView):

    model = Report
    success_url = reverse_lazy("report_index")


class PlayReportView(View):

    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super(PlayReportView, self).dispatch(*args, **kwargs)

    def get(self, request):
        if not url_get_report_id(request):
            return PlayReportView.render(request)
        report = get_object_or_404(Report, pk=url_get_report_id(request))
        return PlayReportView.render_with_sql(request, report.sql)

    def post(self, request):
        sql = request.POST.get('sql', None)
        if not sql:
            return PlayReportView.render(request)
        return PlayReportView.render_with_sql(request, sql)

    @staticmethod
    def render(request):
        c = RequestContext(request, {'title': 'Playground'})
        return render_to_response('report/play.html', c)

    @staticmethod
    def render_with_sql(request, sql):
        report = Report(sql=sql)
        headers, data, error = report.headers_and_data()
        c = RequestContext(request, {
            'error': error,
            'title': 'Playground',
            'sql': sql,
            'data': data[:url_get_rows(request)],
            'headers': headers,
            'rows': url_get_rows(request),
            'total_rows': len(data)})
        return render_to_response('report/play.html', c)


class ReportView(View):

    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super(ReportView, self).dispatch(*args, **kwargs)

    def get(self, request, report_id):
        report, form = ReportView.get_instance_and_form(request, report_id)
        return ReportView.render(request, report, form, None)

    def post(self, request, report_id):
        report, form = ReportView.get_instance_and_form(request, report_id)
        success = form.save() if form.is_valid() else None
        return ReportView.render(request, report, form, "Report saved." if success else None)

    @staticmethod
    def get_instance_and_form(request, report_id):
        report = get_object_or_404(Report, pk=report_id)
        form = ReportForm(request.POST if len(request.POST) else None, instance=report)
        return report, form

    @staticmethod
    def render(request, report, form, message):
        rows = url_get_rows(request)
        headers, data, error = report.headers_and_data()
        c = RequestContext(request, {
            'error': error,
            'report': report,
            'title': report.title,
            'form': form,
            'message': message,
            'data': data[:rows],
            'headers': headers,
            'rows': rows,
            'total_rows': len(data)}
        )
        return render_to_response('report/report.html', c)