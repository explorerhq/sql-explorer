from django.contrib import admin
from explorer.models import Query
from explorer.actions import generate_report_action


class QueryAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'created_by_user',)
    list_filter = ('title',)
    raw_id_fields = ('created_by_user',)
    
    actions = [generate_report_action()]

admin.site.register(Query, QueryAdmin)
