# -*- coding: utf-8 -*-

from django.db import DatabaseError
from django.http import HttpResponse

from explorer.exporters import get_exporter_class
from explorer.utils import url_get_params


def _export(request, query, download=True):
    _fmt = request.GET.get('format', 'csv')
    exporter_class = get_exporter_class(_fmt)
    query.params = url_get_params(request)
    delim = request.GET.get('delim')
    exporter = exporter_class(query)
    try:
        output = exporter.get_output(delim=delim)
    except DatabaseError as e:
        msg = f"Error executing query {query.title}: {e}"
        return HttpResponse(
            msg, status=500
        )

    response = HttpResponse(
        output,
        content_type=exporter.content_type
    )
    if download:
        response['Content-Disposition'] = \
            f'attachment; filename="{exporter.get_filename()}"'
    return response
