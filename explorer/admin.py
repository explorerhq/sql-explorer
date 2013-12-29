from django.contrib import admin
from explorer.models import Query
from explorer.actions import generate_report_action


class QueryAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'created_by',)
    list_filter = ('title',)
    
    actions = [generate_report_action()]

admin.site.register(Query, QueryAdmin)
