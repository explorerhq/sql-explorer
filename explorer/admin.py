from django.db import DatabaseError
from django.contrib import admin
from django.contrib.admin import AdminSite
from explorer.models import Query
from explorer.actions import generate_report_action


class QueryAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'created_by_user',)
    list_filter = ('title',)
    raw_id_fields = ('created_by_user',)
    
    actions = [generate_report_action()]

admin.site.register(Query, QueryAdmin)


class MyAdminSite(AdminSite):
    def handle_uncaught_exception(self, request, resolver, exc_info):
        # Call the parent implementation of handle_uncaught_exception
        response = super().handle_uncaught_exception(request, resolver, exc_info)

        # Check if the exception was a database error
        if isinstance(exc_info[1], DatabaseError):
            # Construct a response that displays a dialog box with a message
            content = '<script>alert("A database error occurred. Please try again later.");</script>'
            response.content = content.encode('utf-8')
            response['Content-Type'] = 'text/html'

        return response
