# -*- coding: utf-8 -*-
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.views import LoginView
from django.core.exceptions import ImproperlyConfigured

from explorer import permissions, app_settings


class PermissionRequiredMixin:

    permission_required = None

    @staticmethod
    def handle_no_permission(request):
        return app_settings.EXPLORER_NO_PERMISSION_VIEW()(request)

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


class SafeLoginView(LoginView):
    template_name = 'admin/login.html'


def safe_login_view_wrapper(request):
    return SafeLoginView.as_view(
        extra_context={
            'title': 'Log in',
            REDIRECT_FIELD_NAME: request.get_full_path()
        }
    )(request)
