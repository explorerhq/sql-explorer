from django import template
from django.utils.module_loading import import_string

from .. import app_settings


register = template.Library()


@register.inclusion_tag('explorer/export_buttons.html')
def export_buttons(query=None):
    exporters = []
    for name, classname in app_settings.EXPLORER_DATA_EXPORTERS:
        exporter_class = import_string(classname)
        exporters.append((name, exporter_class.name))
    return {
        'exporters': exporters,
        'query': query,
    }
