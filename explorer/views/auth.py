# -*- coding: utf-8 -*-
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth.views import redirect_to_login

from explorer import permissions


class PermissionRequiredMixin:

    permission_required = None

    @staticmethod
    def handle_no_permission(request):
        return redirect_to_login(request.get_full_path())
    
    def get_permission_required(self):
        if self.permission_required is None:
            raise ImproperlyConfigured(
                '{0} is missing the permission_required attribute. '
                'Define {0}.permission_required, or override '
                '{0}.get_permission_required().'.format(
                    self.__class__.__name__
                )
            )
        return self.permission_required

    def has_permission(self, request, *args, **kwargs):
        perms = self.get_permission_required()

        # TODO: fix the case when the perms is not defined in
        #  permissions module.
        handler = getattr(permissions, perms)
        return handler(request, *args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        if not self.has_permission(request, *args, **kwargs):
            return self.handle_no_permission(request)
        return super().dispatch(request, *args, **kwargs)
