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


@staff_member_required
def download_report(request, report_id):
    try:
        report = Report.objects.get(pk=report_id)
        fn = generate_report_action()
        return fn(None, None, [report, ])
    except Report.DoesNotExist:
        raise Http404


class CreateReportView(CreateView):

    form_class = ReportForm
    template_name = 'report/report.html'
    model = Report


class PlayReportView(View):

    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super(PlayReportView, self).dispatch(*args, **kwargs)

    def get(self, request):
        c = RequestContext(request)
        return render_to_response('report/play.html', c)

    def post(self, request):
        sql = request.POST.get('sql', None)
        if sql:
            report = Report(sql=sql)
            rows = int(request.GET.get("rows", "100"))
            headers, data, error = report.headers_and_data()
            c = RequestContext(request, {
                'error': error,
                'sql': sql,
                'data': data[:rows],
                'headers': headers,
                'rows': rows,
                'total_rows': len(data)}
            )
        return render_to_response('report/play.html', c)

class ReportView(View):

    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super(ReportView, self).dispatch(*args, **kwargs)

    def get(self, request, report_id):
        message = "Here is your report"
        report, form = ReportView.get_instance_and_form(request, report_id, Http404)
        return ReportView.render(request, report, form, message)

    def post(self, request, report_id):
        report, form = ReportView.get_instance_and_form(request, report_id, HttpResponseServerError)
        message = "Report saved" if form.save() else "There were errors while saving the report"
        return ReportView.render(request, report, form, message)

    @staticmethod
    def get_instance_and_form(request, report_id, ex):
        try:
            report = Report.objects.get(pk=report_id)
        except Report.DoesNotExist:
            raise ex
        form = ReportForm(request.POST if len(request.POST) else None, instance=report)
        return report, form

    @staticmethod
    def render(request, report, form, message):
        rows = int(request.GET.get("rows", "100"))
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