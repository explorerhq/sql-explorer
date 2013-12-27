import functools
from report import app_settings
from django.shortcuts import _get_queryset


def passes_blacklist(sql):
    clean = functools.reduce(lambda sql, term: sql.upper().replace(term, ""), app_settings.SQL_WHITELIST, sql)
    return not any(write_word in clean.upper() for write_word in app_settings.SQL_BLACKLIST)


# enthusiastically borrowed from django-annoying
def get_object_or_None(klass, *args, **kwargs):
    queryset = _get_queryset(klass)
    try:
        return queryset.get(*args, **kwargs)
    except queryset.model.DoesNotExist:
        return None


def safe_cast(val, to_type, default=None):
    try:
        return to_type(val)
    except ValueError:
        return default


def get_int_from_request(request, name, default):
    val = request.GET.get(name, default)
    return safe_cast(val, int, default) if val else val  # handle None defaults


def url_get_rows(request):
    return get_int_from_request(request, 'rows', app_settings.REPORT_DEFAULT_ROWS)


def url_get_report_id(request):
    return get_int_from_request(request, 'report_id', None)