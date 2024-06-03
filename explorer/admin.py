from django.contrib import admin

from explorer.actions import generate_report_action
from explorer.models import Query, ExplorerValue
from explorer.ee.db_connections.admin import DatabaseConnectionAdmin  # noqa


@admin.register(Query)
class QueryAdmin(admin.ModelAdmin):
    list_display = ("title", "description", "created_by_user",)
    list_filter = ("title",)
    raw_id_fields = ("created_by_user",)
    actions = [generate_report_action()]


@admin.register(ExplorerValue)
class ExplorerValueAdmin(admin.ModelAdmin):
    list_display = ("key", "value", "display_key")
    list_filter = ("key",)
    search_fields = ("key", "value")

    def display_key(self, obj):
        # Human-readable name for the key
        return dict(ExplorerValue.EXPLORER_SETTINGS_CHOICES).get(obj.key, "")

    display_key.short_description = "Setting Name"
