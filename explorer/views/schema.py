# -*- coding: utf-8 -*-
from django.http import Http404
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.clickjacking import xframe_options_sameorigin

from explorer.connections import connections
from explorer.schema import schema_info
from explorer.views.auth import PermissionRequiredMixin


class SchemaView(PermissionRequiredMixin, View):

    permission_required = 'change_permission'

    @method_decorator(xframe_options_sameorigin)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        connection = kwargs.get('connection', '')
        if connection not in connections:
            raise Http404
        schema = schema_info(connection)
        if schema:
            return render(
                request,
                'explorer/schema.html',
                {'schema': schema_info(connection)}
            )
        else:
            return render(request, 'explorer/schema_building.html')
