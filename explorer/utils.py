import re
from collections import deque
from typing import Iterable, Tuple

from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView

import sqlparse
from sqlparse import format as sql_format
from sqlparse.sql import Token, TokenList
from sqlparse.tokens import Keyword

from explorer import app_settings


EXPLORER_PARAM_TOKEN = "$$"


def passes_blacklist(sql: str) -> Tuple[bool, Iterable[str]]:
    sql_strings = sqlparse.split(sql)
    keyword_tokens = set()
    for sql_string in sql_strings:
        statements = sqlparse.parse(sql_string)
        for statement in statements:
            for token in walk_tokens(statement):
                if not token.is_whitespace and not isinstance(token, TokenList):
                    if token.ttype in Keyword:
                        keyword_tokens.add(str(token.value).upper())

    fails = [
        bl_word
        for bl_word in app_settings.EXPLORER_SQL_BLACKLIST
        if bl_word.upper() in keyword_tokens
    ]

    return not bool(fails), fails


def walk_tokens(token: TokenList) -> Iterable[Token]:
    """
    Generator to walk all tokens in a Statement
    https://stackoverflow.com/questions/54982118/parse-case-when-statements-with-sqlparse
    :param token: TokenList
    """
    queue = deque([token])
    while queue:
        token = queue.popleft()
        if isinstance(token, TokenList):
            queue.extend(token)
        yield token


def _format_field(field):
    return field.get_attname_column()[1], field.get_internal_type()


def param(name):
    return f"{EXPLORER_PARAM_TOKEN}{name}{EXPLORER_PARAM_TOKEN}"


def swap_params(sql, params):
    p = params.items() if params else {}
    for k, v in p:
        fmt_k = re.escape(str(k).lower())
        regex = re.compile(rf"\$\${fmt_k}(?:\|([^\$\:]+))?(?:\:([^\$]+))?\$\$", re.I)
        sql = regex.sub(str(v), sql)
    return sql


def extract_params(text):
    regex = re.compile(r"\$\$([a-z0-9_]+)(?:\|([^\$\:]+))?(?:\:([^\$]+))?\$\$", re.IGNORECASE)
    params = re.findall(regex, text)
    # Matching will result to ('name', 'label', 'default')
    return {
        p[0].lower(): {
            "label": p[1],
            "default": p[2]
        } for p in params if len(p) > 1
    }


def safe_login_prompt(request):
    defaults = {
        "template_name": "admin/login.html",
        "authentication_form": AuthenticationForm,
        "extra_context": {
            "title": "Log in",
            "app_path": request.get_full_path(),
            REDIRECT_FIELD_NAME: request.get_full_path(),
        },
    }
    return LoginView.as_view(**defaults)(request)


def shared_dict_update(target, source):
    for k_d1 in target:
        if k_d1 in source:
            target[k_d1] = source[k_d1]
    return target


def safe_cast(val, to_type, default=None):
    try:
        return to_type(val)
    except ValueError:
        return default


def get_int_from_request(request, name, default):
    val = request.GET.get(name, default)
    return safe_cast(val, int, default) if val else None


def get_params_from_request(request):
    val = request.GET.get("params", None)
    try:
        d = {}
        tuples = val.split("|")
        for t in tuples:
            res = t.split(":")
            d[res[0]] = res[1]
        return d
    except Exception:
        return None


def get_params_for_url(query):
    if query.params:
        return "|".join([f"{p}:{v}" for p, v in query.params.items()])


def url_get_rows(request):
    return get_int_from_request(
        request, "rows", app_settings.EXPLORER_DEFAULT_ROWS
    )


def url_get_query_id(request):
    return get_int_from_request(request, "query_id", None)


def url_get_log_id(request):
    return get_int_from_request(request, "querylog_id", None)


def url_get_show(request):
    return bool(get_int_from_request(request, "show", 1))


def url_get_fullscreen(request):
    return bool(get_int_from_request(request, "fullscreen", 0))


def url_get_params(request):
    return get_params_from_request(request)


def allowed_query_pks(user_id):
    return app_settings.EXPLORER_GET_USER_QUERY_VIEWS().get(user_id, [])


def user_can_see_query(request, **kwargs):
    if not request.user.is_anonymous and "query_id" in kwargs:
        return int(kwargs["query_id"]) in allowed_query_pks(request.user.id)
    return False


def fmt_sql(sql):
    return sql_format(sql, reindent=True, keyword_case="upper")


def noop_decorator(f):
    return f


class InvalidExplorerConnectionException(Exception):
    pass


def get_valid_connection(alias=None):
    from explorer.connections import connections

    if not alias:
        return connections()[app_settings.EXPLORER_DEFAULT_CONNECTION]

    if alias not in connections():
        raise InvalidExplorerConnectionException(
            f"Attempted to access connection {alias}, "
            f"but that is not a registered Explorer connection."
        )
    return connections()[alias]


def delete_from_s3(s3_path):
    s3_bucket = get_s3_bucket()
    s3_bucket.delete_objects(
        Delete={
            "Objects": [
                {"Key": s3_path}
            ]
        }
    )


def get_s3_bucket():
    import boto3
    from botocore.client import Config

    config = Config(
        signature_version=app_settings.S3_SIGNATURE_VERSION,
        region_name=app_settings.S3_REGION
    )

    kwargs = {"config": config}

    # If these are set, use them. Otherwise, boto will use its built-in mechanisms
    # to provide authentication.
    if app_settings.S3_ACCESS_KEY and app_settings.S3_SECRET_KEY:
        kwargs["aws_access_key_id"] = app_settings.S3_ACCESS_KEY
        kwargs["aws_secret_access_key"] = app_settings.S3_SECRET_KEY

    if app_settings.S3_ENDPOINT_URL:
        kwargs["endpoint_url"] = app_settings.S3_ENDPOINT_URL

    s3 = boto3.resource("s3", **kwargs)

    return s3.Bucket(name=app_settings.S3_BUCKET)


def s3_upload(key, data):
    if app_settings.S3_DESTINATION:
        key = "/".join([app_settings.S3_DESTINATION, key])
    bucket = get_s3_bucket()
    bucket.upload_fileobj(data, key, ExtraArgs={"ContentType": "text/csv"})
    return s3_url(bucket, key)


def s3_url(bucket, key):
    url = bucket.meta.client.generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": app_settings.S3_BUCKET, "Key": key},
        ExpiresIn=app_settings.S3_LINK_EXPIRATION)
    return url


def is_xls_writer_available():
    try:
        import xlsxwriter  # noqa
        return True
    except ImportError:
        return False
