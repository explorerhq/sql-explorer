from explorer.utils import (
    passes_blacklist,
    swap_params,
    extract_params,
    shared_dict_update,
    get_connection,
    get_s3_connection,
    get_connection_pii,
    get_explorer_master_db_connection,
    get_connection_asyncapi_db,
    should_route_to_asyncapi_db,
    mask_string,
    is_pii_masked_for_user,
    mask_player_pii,
)
from django.db import models, DatabaseError
from time import time
from django.urls import reverse
from django.conf import settings
from django.contrib import messages
from django.contrib.messages import constants as messages_constants
from . import app_settings
import logging
import re
import json
import six

from explorer.constants import (
    TYPE_CODE_FOR_JSON,
    TYPE_CODE_FOR_TEXT,
    PLAYER_PHONE_NUMBER_MASKING_TYPE_CODES,
    TYPE_CODE_FOR_CHAR,
)

MSG_FAILED_BLACKLIST = "Query failed the SQL blacklist: %s"


logger = logging.getLogger(__name__)


class Query(models.Model):
    title = models.CharField(max_length=255)
    sql = models.TextField()
    description = models.TextField(null=True, blank=True)
    created_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_run_date = models.DateTimeField(auto_now=True)
    snapshot = models.BooleanField(
        default=False, help_text="Include in snapshot task (if enabled)"
    )

    def __init__(self, *args, **kwargs):
        self.params = kwargs.get("params")
        kwargs.pop("params", None)
        super(Query, self).__init__(*args, **kwargs)

    class Meta:
        ordering = ["title"]
        verbose_name_plural = "Queries"

    def __str__(self):
        return self.title

    def get_run_count(self):
        return self.querylog_set.count()

    def avg_duration(self):
        return self.querylog_set.aggregate(models.Avg("duration"))["duration__avg"]

    def passes_blacklist(self):
        return passes_blacklist(self.final_sql())

    def final_sql(self):
        return swap_params(self.sql, self.available_params())

    def execute_query_only(
        self,
        is_connection_type_pii=None,
        executing_user=None,
        is_connection_for_explorer_master_db=False,
    ):
        return QueryResult(
            self.final_sql(),
            self.title,
            is_connection_type_pii,
            executing_user if executing_user else self.created_by_user,
            is_connection_for_explorer_master_db,
        )

    def execute_with_logging(self, executing_user):
        ql = self.log(executing_user)
        ret = self.execute(executing_user)
        ql.duration = ret.duration
        ql.save()
        return ret, ql

    def execute(self, executing_user=None):
        ret = self.execute_query_only(False, executing_user)
        ret.process()
        return ret

    def execute_pii(self, executing_user=None):
        ret = self.execute_query_only(True, executing_user)
        ret.process()
        return ret

    def execute_on_explorer_with_master_db(self, executing_user=None):
        ret = self.execute_query_only(
            False, executing_user, is_connection_for_explorer_master_db=True
        )
        ret.process()
        return ret

    def available_params(self):
        """
            Merge parameter values into a dictionary of available parameters

        :param param_values: A dictionary of Query param values.
        :return: A merged dictionary of parameter names and values. Values of non-existent parameters are removed.
        """

        p = extract_params(self.sql)
        if self.params:
            shared_dict_update(p, self.params)
        return p

    def get_absolute_url(self):
        return reverse("query_detail", kwargs={"query_id": self.id})

    def log(self, user=None):

        if user:
            # In Django<1.10, is_anonymous was a method.
            if user.is_anonymous:
                user = None
        ql = QueryLog(
            sql=self.final_sql(),
            query_id=self.id,
            run_by_user=user,
        )
        ql.save()
        return ql


    @property
    def shared(self):
        return self.id in set(
            sum(app_settings.EXPLORER_GET_USER_QUERY_VIEWS().values(), [])
        )

    @property
    def snapshots(self):
        if app_settings.ENABLE_TASKS:
            conn = get_s3_connection()
            res = conn.list("query-%s.snap-" % self.id)
            return sorted(res, key=lambda s: s["last_modified"])


class QueryLog(models.Model):

    sql = models.TextField(null=True, blank=True)
    query = models.ForeignKey(Query, null=True, blank=True, on_delete=models.SET_NULL)
    run_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE
    )
    run_at = models.DateTimeField(auto_now_add=True)
    duration = models.FloatField(blank=True, null=True)  # milliseconds

    @property
    def is_playground(self):
        return self.query_id is None

    class Meta:
        ordering = ["-run_at"]


class QueryChangeLog(models.Model):

    old_sql = models.TextField(null=True, blank=True)
    new_sql = models.TextField(null=True, blank=True)
    query = models.ForeignKey(Query, null=True, blank=True, on_delete=models.SET_NULL)
    run_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE
    )
    run_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_playground(self):
        return self.query_id is None

    class Meta:
        ordering = ["-run_at"]


class QueryResult(object):
    def get_type_code_and_column_indices_to_be_masked_dict(self):
        """
        Returns a dictionary of type code and column indices to be masked
        Return type:
        {
            type_code: [column indices that match the type code]
        }
        Eg.
        Say a table has three fields id, data, random_text. id is of type INT, data is of type JSON, and random_text is of type TEXT.
        Then the return value will be:
        {
            TYPE_CODE_FOR_JSON: [1],
            TYPE_CODE_FOR_TEXT: [2]
        }
        as 1 is the column index for JSON and 2 is the column index for TEXT
        """
        type_code_and_column_indices_to_be_masked_dict = {
            TYPE_CODE_FOR_JSON: [],
            TYPE_CODE_FOR_TEXT: [],
        }
        phone_number_masking_indexes = []

        # Collect the indices for JSON and text columns
        for index, column in enumerate(self._description):
            if (
                hasattr(column, "type_code")
                and column.type_code in type_code_and_column_indices_to_be_masked_dict
            ):
                type_code_and_column_indices_to_be_masked_dict[column.type_code].append(
                    index
                )

            # Masking for player phone numbers
            if (
                self.used_by_user
                and is_pii_masked_for_user(self.used_by_user)
                and hasattr(column, "type_code")
                and column.type_code in PLAYER_PHONE_NUMBER_MASKING_TYPE_CODES
            ):
                phone_number_masking_indexes.append(index)

        # Masking for PII data in char fields if specific tables are used in SQL
        if app_settings.TABLE_NAMES_FOR_PII_MASKING and phone_number_masking_indexes:
            for table_name in app_settings.TABLE_NAMES_FOR_PII_MASKING:
                if table_name in self.sql:
                    type_code_and_column_indices_to_be_masked_dict[
                        TYPE_CODE_FOR_CHAR
                    ] = phone_number_masking_indexes
                    break

        return type_code_and_column_indices_to_be_masked_dict

    def get_masked_data(self, data, type_code):
        """
        Mask the data based on the type code.
        """
        if not data:
            return data
        if type_code == TYPE_CODE_FOR_JSON:
            return json.dumps(mask_string(str(data)))
        elif type_code == TYPE_CODE_FOR_TEXT:
            return mask_string(data)
        elif type_code in PLAYER_PHONE_NUMBER_MASKING_TYPE_CODES:
            return mask_player_pii(data)
        return data

    def mask_pii_data(self, row, type_code_and_column_indices_to_be_masked_dict):
        """
        Mask the JSON and TEXT data types in the row.
        """
        modified_row = list(row)
        for (
            type_code,
            indices,
        ) in type_code_and_column_indices_to_be_masked_dict.items():
            for index in indices:
                modified_row[index] = self.get_masked_data(
                    modified_row[index], type_code
                )

        return modified_row

    def get_data_to_be_displayed(self, cursor):
        """
        If the connection type allows PII, then return the data as is.
        If connection type does not allow PII, then mask JSON and TEXT data types and then return the data.
        JSON and TEXT data types can be identified by the type_code attribute of the column.
        """
        if self.is_connection_type_pii:
            return [list(r) for r in cursor.fetchall()]

        type_code_and_column_indices_to_be_masked_dict = (
            self.get_type_code_and_column_indices_to_be_masked_dict()
        )
        data_to_be_displayed = []

        for row in cursor.fetchall():
            modified_row = self.mask_pii_data(
                row, type_code_and_column_indices_to_be_masked_dict
            )
            data_to_be_displayed.append(modified_row)

        return data_to_be_displayed

    def __init__(
        self,
        sql,
        title=None,
        is_connection_type_pii=None,
        used_by_user=None,
        is_connection_for_explorer_master_db=False,
    ):

        self.sql = sql
        self.title = title
        self.is_connection_for_explorer_master_db = is_connection_for_explorer_master_db
        if is_connection_type_pii:
            self.is_connection_type_pii = is_connection_type_pii
        else:
            self.is_connection_type_pii = False

        self.used_by_user = used_by_user
        cursor, duration = self.execute_query()

        self._description = cursor.description or []

        self._data = self.get_data_to_be_displayed(cursor)

        self.duration = duration
        cursor.close()

        self._headers = self._get_headers()
        self._summary = {}

    @property
    def data(self):
        return self._data or []

    @property
    def headers(self):
        return self._headers or []

    def _get_headers(self):
        return (
            [ColumnHeader(d[0]) for d in self._description]
            if self._description
            else [ColumnHeader("--")]
        )

    def _get_numerics(self):
        conn = get_connection()
        if hasattr(conn.Database, "NUMBER"):
            return [
                ix
                for ix, c in enumerate(self._description)
                if hasattr(c, "type_code")
                and c.type_code in conn.Database.NUMBER.values
            ]
        elif self.data:
            d = self.data[0]
            return [
                ix
                for ix, _ in enumerate(self._description)
                if not isinstance(d[ix], six.string_types)
                and six.text_type(d[ix]).isnumeric()
            ]
        return []

    def _get_transforms(self):
        transforms = dict(app_settings.EXPLORER_TRANSFORMS)
        return [
            (ix, transforms[str(h)])
            for ix, h in enumerate(self.headers)
            if str(h) in transforms.keys()
        ]

    def column(self, ix):
        return [r[ix] for r in self.data]

    def process(self):
        start_time = time()

        self.process_columns()
        self.process_rows()

        logger.info(
            "Explorer test Query Processing took %sms." % ((time() - start_time) * 1000)
        )

    def process_columns(self):
        for ix in self._get_numerics():
            self.headers[ix].add_summary(self.column(ix))

    def process_rows(self):
        transforms = self._get_transforms()
        if transforms:
            for r in self.data:
                for ix, t in transforms:
                    r[ix] = t.format(str(r[ix]))

    def execute_query(self):
        # can change connectiion type here to use different role --> get_connection_pii()
        if self.is_connection_type_pii:
            logger.info("pii-connection")
            conn = get_connection_pii()
        elif should_route_to_asyncapi_db(self.sql):
            logger.info("Route to Async API DB")
            conn = get_connection_asyncapi_db()
        elif self.is_connection_for_explorer_master_db:
            conn = get_explorer_master_db_connection()
        else:
            logger.info("non-pii-connection")
            conn = get_connection()

        cursor = conn.cursor()
        start_time = time()

        try:
            cursor.execute(self.sql)
        except DatabaseError as e:
            cursor.close()
            if (
                re.search("permission denied for table", str(e))
                and self.title != "Playground"
            ):

                raise DatabaseError(
                    "Query saved but unable to execute it because " + str(e)
                )
            else:
                raise e

        return cursor, ((time() - start_time) * 1000)


class ColumnHeader(object):

    def __init__(self, title):
        self.title = title.strip()
        self.summary = None

    def add_summary(self, column):
        self.summary = ColumnSummary(self, column)

    def __unicode__(self):
        return self.title

    def __str__(self):
        return self.title


class ColumnStat(object):

    def __init__(self, label, statfn, precision=2, handles_null=False):
        self.label = label
        self.statfn = statfn
        self.precision = precision
        self.handles_null = handles_null

    def __call__(self, coldata):
        self.value = (
            round(float(self.statfn(coldata)), self.precision) if coldata else 0
        )

    def __unicode__(self):
        return self.label

    def foo(self):
        return "foobar"


class ColumnSummary(object):

    def __init__(self, header, col):
        self._header = header
        self._stats = [
            ColumnStat("Sum", sum),
            ColumnStat("Avg", lambda x: float(sum(x)) / float(len(x))),
            ColumnStat("Min", min),
            ColumnStat("Max", max),
            ColumnStat(
                "NUL",
                lambda x: int(sum(map(lambda y: 1 if y is None else 0, x))),
                0,
                True,
            ),
        ]
        without_nulls = list(map(lambda x: 0 if x is None else x, col))

        for stat in self._stats:
            stat(col) if stat.handles_null else stat(without_nulls)

    @property
    def stats(self):
        # dict comprehensions are not supported in Python 2.6, so do this instead
        return dict((c.label, c.value) for c in self._stats)

    def __str__(self):
        return str(self._header)
