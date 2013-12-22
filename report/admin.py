from django.contrib import admin
from report.models import Report
from report.actions import generate_report_action

class ReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'created_by',)
    list_filter = ('title',)
    
    actions = [generate_report_action()]

admin.site.register(Report, ReportAdmin)

