from django import template
from django.utils.module_loading import import_string

from explorer import app_settings


register = template.Library()


@register.inclusion_tag("explorer/export_buttons.html")
def export_buttons(query=None):
    exporters = []
    for name, classname in app_settings.EXPLORER_DATA_EXPORTERS:
        exporter_class = import_string(classname)
        exporters.append((name, exporter_class.name))
    return {
        "exporters": exporters,
        "query": query,
    }


@register.inclusion_tag("explorer/query_favorite_button.html")
def query_favorite_button(query_id, is_favorite, extra_classes):
    return {
        "query_id": query_id,
        "is_favorite": is_favorite,
        "extra_classes": extra_classes
    }
