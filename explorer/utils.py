from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.views import login
from django.contrib.admin.forms import AdminAuthenticationForm
import datetime
import sqlparse
from ago import human
from six.moves import cStringIO
from django.http import HttpResponse
from django.db import connections, connection, DatabaseError
from explorer import app_settings
import string
import re
import functools
import sys
import logging

from explorer.constants import PII_MASKING_PATTERN_REPLACEMENT_DICT, ALLOW_PHONE_NUMBER_MASKING_GROUP_ID, \
    PATTERN_FOR_FINDING_EMAIL, PATTERN_FOR_FINDING_PHONE_NUMBER

logger = logging.getLogger(__name__)

PY3 = sys.version_info[0] == 3

if PY3:
    import csv
else:
    import unicodecsv as csv

EXPLORER_PARAM_TOKEN = "$$"

REPLICATION_LAG_THRESHOLD_VALUE_IN_MINUTES = 3


# SQL Specific Things


def passes_blacklist(sql):
    clean = functools.reduce(lambda sql, term: sql.upper().replace(term, ""), [
        t.upper() for t in app_settings.EXPLORER_SQL_WHITELIST], sql)
    fails = [
        bl_word for bl_word in app_settings.EXPLORER_SQL_BLACKLIST if bl_word in clean.upper()]
    return not any(fails), fails


def get_connection():
    logger.info("explorer_connection succesfull")
    return connections[app_settings.EXPLORER_CONNECTION_NAME] if app_settings.EXPLORER_CONNECTION_NAME else connection


def get_explorer_master_db_connection():
    logger.info("get_explorer_master_db_connection successful")
    return connections[
        app_settings.EXPLORER_MASTER_DB_CONNECTION_NAME] if app_settings.EXPLORER_MASTER_DB_CONNECTION_NAME else connection


def get_connection_pii():
    logger.info("explorer_pii_connection succesfull")
    return connections[app_settings.EXPLORER_CONNECTION_PII_NAME] if app_settings.EXPLORER_CONNECTION_PII_NAME else connection


def get_master_db_connection():
    logger.info("explorer_pii_connection succesfull")
    return connections[
        app_settings.EXPLORER_CONNECTION_PII_NAME] if app_settings.EXPLORER_CONNECTION_PII_NAME else connection


def get_connection_asyncapi_db():
    logger.info("Connecting with async-api DB")
    return connections[
        app_settings.EXPLORER_CONNECTION_ASYNC_API_DB_NAME] if app_settings.EXPLORER_CONNECTION_ASYNC_API_DB_NAME else connection


def schema_info():
    """
    Construct schema information via introspection of the django models in the database.

    :return: Schema information of the following form, sorted by db_table_name.
        [
            ("package.name -> ModelClass", "db_table_name",
                [
                    ("db_column_name", "DjangoFieldType"),
                    (...),
                ]
            )
        ]

    """

    from django.apps import apps
    import logging

    logger = logging.getLogger(__name__)

    ret = []

    for label, app in apps.app_configs.items():
        if app.name not in app_settings.EXPLORER_SCHEMA_EXCLUDE_APPS:
            for model_name, model in apps.get_app_config(label).models.items():
                friendly_model = "%s -> %s" % (app.name, model._meta.object_name)
                ret.append((
                    friendly_model,
                    model._meta.db_table,
                    [_format_field(f) for f in model._meta.fields]
                ))

                try:
                    # Loop over Many-to-Many relationships
                    for m2m in model._meta.many_to_many:
                        through_model = m2m.remote_field.through
                        ret.append(
                            (
                                friendly_model,
                                through_model._meta.db_table,
                                [
                                    _format_field(f)
                                    for f in through_model._meta.fields
                                ],
                            )
                        )
                except Exception as e:
                    logger.error(
                        "Error while processing Many-to-Many relationships: %s" % e
                    )

    return sorted(ret, key=lambda t: t[1])


def _format_field(field):
    return field.get_attname_column()[1], field.get_internal_type()


def param(name):
    return "%s%s%s" % (EXPLORER_PARAM_TOKEN, name, EXPLORER_PARAM_TOKEN)


def swap_params(sql, params):
    p = params.items() if params else {}
    for k, v in p:
        regex = re.compile("\$\$%s(?:\:([^\$]+))?\$\$" % str(k))
        sql = regex.sub(str(v), sql)
    return sql


def extract_params(text):
    regex = re.compile("\$\$([a-z0-9_]+)(?:\:([^\$]+))?\$\$")
    params = re.findall(regex, text)
    # We support Python 2.6 so can't use a dict comprehension
    return dict(zip([p[0] for p in params], [p[1] if len(p) > 1 else '' for p in params]))


def write_csv(headers, data, delim=None):
    if delim and len(delim) == 1 or delim == 'tab':
        delim = '\t' if delim == 'tab' else str(delim)
    else:
        delim = app_settings.CSV_DELIMETER
    csv_data = cStringIO()
    if PY3:
        writer = csv.writer(csv_data, delimiter=delim)
    else:
        writer = csv.writer(csv_data, delimiter=delim, encoding='utf-8')
    writer.writerow(headers)
    for row in data:
        writer.writerow([s for s in row])
    return csv_data


def get_filename_for_title(title):
    # build list of valid chars, build filename from title and replace spaces
    valid_chars = '-_.() %s%s' % (string.ascii_letters, string.digits)
    filename = ''.join(c for c in title if c in valid_chars)
    filename = filename.replace(' ', '_')
    return filename


def build_stream_response(query, delim=None, user=None):
    data = csv_report(query, delim, user).getvalue()
    response = HttpResponse(data, content_type='text')
    return response


def build_download_response(query, delim=None, user=None):
    data = csv_report(query, delim, user).getvalue()
    response = HttpResponse(data, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s.csv"' % (
        get_filename_for_title(query.title)
    )
    response['Content-Length'] = len(data)
    return response


def csv_report(query, delim=None, user=None):
    try:
        res = query.execute_query_only(executing_user=user)
        return write_csv(res.headers, res.data, delim)
    except DatabaseError as e:
        return str(e)


# Helpers


def safe_admin_login_prompt(request):
    defaults = {
        'template_name': 'admin/login.html',
        'authentication_form': AdminAuthenticationForm,
        'extra_context': {
            'title': 'Log in',
            'app_path': request.get_full_path(),
            REDIRECT_FIELD_NAME: request.get_full_path(),
        },
    }
    return login(request, **defaults)


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
    val = request.GET.get('params', None)
    try:
        d = {}
        tuples = val.split('|')
        for t in tuples:
            res = t.split(':')
            d[res[0]] = res[1]
        return d
    except Exception:
        return None


def url_get_rows(request):
    return get_int_from_request(request, 'rows', app_settings.EXPLORER_DEFAULT_ROWS)


def url_get_query_id(request):
    return get_int_from_request(request, 'query_id', None)


def url_get_log_id(request):
    return get_int_from_request(request, 'querylog_id', None)


def url_get_show(request):
    return bool(get_int_from_request(request, 'show', 1))


def url_get_params(request):
    return get_params_from_request(request)


def allowed_query_pks(user_id):
    return app_settings.EXPLORER_GET_USER_QUERY_VIEWS().get(user_id, [])


def user_can_see_query(request, kwargs):
    if not request.user.is_anonymous() and 'query_id' in kwargs:
        return int(kwargs['query_id']) in allowed_query_pks(request.user.id)
    return False


def fmt_sql(sql):
    return sqlparse.format(sql, reindent=True, keyword_case='upper')


def noop_decorator(f):
    return f


def get_s3_connection():
    import tinys3
    return tinys3.Connection(app_settings.S3_ACCESS_KEY,
                             app_settings.S3_SECRET_KEY,
                             default_bucket=app_settings.S3_BUCKET)


def compare_sql(old_sql, new_sql):
    """
    Compares whether two sql queries are the 
    same after formatting them
    """
    return fmt_sql(old_sql) == fmt_sql(new_sql)


def check_replication_lag():
    """
    Check if a replication lag exists
    :returns: True and the replication lag interval if it 
              exceeds 3 minutes, else returns False and None
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT now() - pg_last_xact_replay_timestamp() AS replication_lag")
    replication_lag = cursor.fetchone()[0]

    threshold_value = datetime.timedelta(
        minutes=REPLICATION_LAG_THRESHOLD_VALUE_IN_MINUTES)

    if not replication_lag or replication_lag <= threshold_value:
        return False, None

    return True, human(replication_lag, 4)


def should_route_to_asyncapi_db(sql):
    request_log_tables = [
        "request_log_requestlog", 
        "request_log_requestlogdata", 
        "temp_request_log_requestlog_customer", 
        "temp_request_log_requestlogdata_customer",
    ]
    pattern = r"\b(?:%s)\b" % "|".join(map(re.escape, request_log_tables))
    match = re.search(pattern, sql)
    if match:
        return True

    return False


def mask_string(string_to_masked):
    """
    Replace a string with a dictionary of regex patterns and replacements
    Param 1: string that needs to be masked

    Eg.
    Following is the PII_MASKING_PATTERN_REPLACEMENT_DICT as of now
    {
        r"(?:\+?\d{1,3}|0)?([6-9]\d{9})\b": "XXXXXXXXXXX", # For masking phone number
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b": "XXX@XXX.com", # For masking email
    }
    It would mask the string:
    'My number is +919191919191, their number is 9191919191, my email is abc@abc.com, their email is xyz@pq.in.'
    to:
    'My number is XXXXXXXXXXX, their number is XXXXXXXXXXX, my email is XXX@XXX.com, their email is XXX@XXX.com.'
    and return it.
    """

    for pattern, replacement in PII_MASKING_PATTERN_REPLACEMENT_DICT.items():
        string_to_masked = re.sub(pattern, replacement, string_to_masked)
    return string_to_masked


def get_masked_value(value: str):
    """
    This function will return the masked value depending upon the length of the value.
    For eg.
    1. value = None => masked_value = None
    1. value = "son" => masked_value = "XXX"
    2. value = "sunny" => masked_value = "sXXXy"
    3. value = "my name is kunal" => masked_value = "myXXXXXXXXXXXal"
    """

    if not value:
        return None

    if len(value) <= 3:
        return "".join("X" for _ in range(len(value)))
    elif 4 <= len(value) <= 5:
        return value[0] + "".join("X" for _ in range(len(value) - 2)) + value[-1]
    else:
        return value[:2] + "".join("X" for _ in range(len(value) - 2)) + value[-2:]


def get_masked_email(email: str) -> str:
    if not email or "@" not in email:
        return email

    local_part, domain_part = email.split("@")
    masked_local_part = get_masked_value(local_part)
    return masked_local_part + "@" + "".join("X" for _ in range(len(domain_part)))


def get_masked_phone_number(phone_number: str) -> str:
    if not phone_number or len(phone_number) < 10:
        return phone_number

    return "".join("X" for _ in range(len(phone_number) - 4)) + phone_number[-4:]


def mask_player_pii(data: str) -> str:
    if not data:
        return data

    matched_phone_numbers = re.findall(PATTERN_FOR_FINDING_PHONE_NUMBER, data)
    for phone_number in matched_phone_numbers:
        data = data.replace(phone_number, get_masked_phone_number(phone_number))

    matched_emails = re.findall(PATTERN_FOR_FINDING_EMAIL, data)
    for email in matched_emails:
        data = data.replace(email, get_masked_email(email))

    return data


def is_pii_masked_for_user(user):
    """
    Check if the user has permission to view masked phone numbers
    """
    user_group_ids = user.groups.all().values_list('id', flat=True)
    return ALLOW_PHONE_NUMBER_MASKING_GROUP_ID not in user_group_ids
