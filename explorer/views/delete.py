# -*- coding: utf-8 -*-
from django.urls import reverse_lazy
from django.views.generic import DeleteView

from explorer.models import Query
from explorer.views.auth import PermissionRequiredMixin
from explorer.views.mixins import ExplorerContextMixin


class DeleteQueryView(PermissionRequiredMixin, ExplorerContextMixin,
                      DeleteView):

    permission_required = 'change_permission'
    model = Query
    success_url = reverse_lazy("explorer_index")
