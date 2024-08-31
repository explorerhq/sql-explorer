from explorer import app_settings
from explorer.utils import allowed_query_pks, user_can_see_query


def view_permission(request, **kwargs):
    return app_settings.EXPLORER_PERMISSION_VIEW(request)\
        or user_can_see_query(request, **kwargs)\
        or (app_settings.EXPLORER_TOKEN_AUTH_ENABLED()
            and (request.headers.get("X-Api-Token") ==
                 app_settings.EXPLORER_TOKEN
                 or request.GET.get("token") == app_settings.EXPLORER_TOKEN))

# Users who can only see some queries can still see the list.
# Different than the above because it's not checking for any specific
# query permissions.
# And token auth does not give you permission to view the list.


def view_permission_list(request, *args, **kwargs):
    return app_settings.EXPLORER_PERMISSION_VIEW(request)\
        or allowed_query_pks(request.user.id)


def change_permission(request, *args, **kwargs):
    return app_settings.EXPLORER_PERMISSION_CHANGE(request)


def connections_permission(request, *args, **kwargs):
    return app_settings.EXPLORER_PERMISSION_CONNECTIONS(request)
