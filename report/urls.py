from django.conf.urls import patterns, url
from django.contrib.admin.views.decorators import staff_member_required
from report.views import ReportView

urlpatterns = patterns('',
    url(r'(?P<report_id>\d+)/$', staff_member_required(ReportView.as_view()), name='report_detail'),
    url(r'(?P<report_id>\d+)/download$', staff_member_required(ReportView.as_view()), name='report_detail'),
    url(r'$', ReportView.as_view(), name='report_index'),
)