from django.contrib import admin
from explorer.models import Query, FTPExport
from explorer.actions import generate_report_action


class QueryAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'created_by_user',)
    list_filter = ('title',)
    raw_id_fields = ('created_by_user',)
    
    actions = [generate_report_action()]


class FTPExportAdmin(admin.ModelAdmin):
    raw_id_fields = ('query',)

admin.site.register(Query, QueryAdmin)
admin.site.register(FTPExport, FTPExportAdmin)
