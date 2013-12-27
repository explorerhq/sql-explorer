from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import Http404, HttpResponseServerError, HttpResponse
from report.actions import generate_report_action
from django.views.generic.base import View
from django.views.generic.edit import CreateView
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from report.models import Report
from report.forms import ReportForm
from report.utils import get_object_or_None, url_get_rows, url_get_report_id


@staff_member_required
def download_report(request, report_id):
    report = get_object_or_None(Report, pk=report_id)
    if not report:
        raise Http404
    fn = generate_report_action()
    return fn(None, None, [report, ])


class CreateReportView(CreateView):

    form_class = ReportForm
    template_name = 'report/report.html'
    model = Report


class PlayReportView(View):

    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super(PlayReportView, self).dispatch(*args, **kwargs)

    def get(self, request):
        if not url_get_report_id(request):
            return PlayReportView.render(request, {})
        report = get_object_or_None(Report, pk=url_get_report_id(request))
        return PlayReportView.render_with_sql(request, report.sql, url_get_rows(request))

    def post(self, request):
        sql = request.POST.get('sql', None)
        if not sql:
            return PlayReportView.render(request, {'error': 'No SQL provided'})
        return PlayReportView.render_with_sql(request, sql, url_get_rows(request))

    @staticmethod
    def render(request, context):
        c = RequestContext(request, context)
        c.update({'title': 'playground'})
        return render_to_response('report/play.html', c)

    @staticmethod
    def render_with_sql(request, sql, rows):
        report = Report(sql=sql)
        headers, data, error = report.headers_and_data()
        c = {'error': error,
             'title': 'playground',
             'sql': sql,
             'data': data[:rows],
             'headers': headers,
             'rows': rows,
             'total_rows': len(data)}
        return PlayReportView.render(request, c)


class ReportView(View):

    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super(ReportView, self).dispatch(*args, **kwargs)

    def get(self, request, report_id):
        report, form = ReportView.get_instance_and_form(request, report_id, Http404)
        return ReportView.render(request, report, form, "Here is your report")

    def post(self, request, report_id):
        report, form = ReportView.get_instance_and_form(request, report_id, HttpResponseServerError)
        message = "Report saved" if form.save() else "There were errors while saving the report"
        return ReportView.render(request, report, form, message)

    @staticmethod
    def get_instance_and_form(request, report_id, ex):
        report = get_object_or_None(Report, pk=report_id)
        if not report:
            raise ex
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