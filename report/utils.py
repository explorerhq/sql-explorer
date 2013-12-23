import functools
from report import app_settings


def passes_blacklist(sql):
    clean = functools.reduce(lambda sql, term: sql.upper().replace(term, ""), app_settings.SQL_WHITELIST, sql)
    return not any(write_word in clean.upper() for write_word in app_settings.SQL_BLACKLIST)