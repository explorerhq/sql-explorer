from django.conf.urls import patterns, url
from report.views import ReportView, CreateReportView, PlayReportView, DeleteReportView, ListReportView

urlpatterns = patterns('',
    url(r'(?P<report_id>\d+)/$', ReportView.as_view(), name='report_detail'),
    url(r'(?P<report_id>\d+)/download$', 'report.views.download_report', name='report_download'),
    url(r'(?P<pk>\d+)/delete$', DeleteReportView.as_view(), name='report_delete'),
    url(r'new/$', CreateReportView.as_view(), name='report_create'),
    url(r'play/$', PlayReportView.as_view(), name='report_playground'),
    url(r'schema/$', 'report.views.schema', name='report_schema'),
    url(r'$', ListReportView.as_view(), name='report_index'),
)