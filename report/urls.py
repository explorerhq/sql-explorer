from django.conf.urls import patterns, url
from django.views.generic import ListView
from report.views import ReportView, CreateReportView
from report.models import Report

urlpatterns = patterns('',
    url(r'(?P<report_id>\d+)/$', ReportView.as_view(), name='report_detail'),
    url(r'new/$', CreateReportView.as_view(), name='report_create'),
    url(r'(?P<report_id>\d+)/download$', 'report.views.download_report', name='report_download'),
    url(r'$', ListView.as_view(model=Report), name='report_index'),
)