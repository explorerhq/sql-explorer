from explorer import app_settings
from explorer.utils import allowed_query_pks, user_can_see_query


def _token_supplied(request):
    """
    Whether the request carries the configured API token.

    The token is a server-wide credential, not a user, so it says nothing about which
    queries the caller is allowed to reach. That is decided by token_can_see_query.
    """
    return app_settings.EXPLORER_TOKEN_AUTH_ENABLED() and (
        request.headers.get("X-Api-Token") == app_settings.EXPLORER_TOKEN
        or request.GET.get("token") == app_settings.EXPLORER_TOKEN
    )


def token_can_see_query(query_id):
    """
    Scope a valid token to the queries it is meant to reach.

    Token auth exists so a script can pull results for queries that have been shared
    with it. When ``EXPLORER_USER_QUERY_VIEWS`` is configured, that is the list of
    shareable queries, so the token is limited to it -- otherwise any token holder
    could read every query by walking query ids. When it is not configured there is no
    such list, and the token keeps the documented access to any query.
    """
    if query_id is None:
        return True
    allowed = set(sum(app_settings.EXPLORER_GET_USER_QUERY_VIEWS().values(), []))
    if not allowed:
        return True
    return int(query_id) in allowed


def view_permission(request, **kwargs):
    return app_settings.EXPLORER_PERMISSION_VIEW(request)\
        or user_can_see_query(request, **kwargs)\
        or (_token_supplied(request)
            and token_can_see_query(kwargs.get("query_id")))

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
