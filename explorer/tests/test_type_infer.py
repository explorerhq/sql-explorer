from django.test import TestCase
from unittest import skipIf
from explorer.app_settings import EXPLORER_USER_UPLOADS_ENABLED
if EXPLORER_USER_UPLOADS_ENABLED:
    import pandas as pd
import os
from explorer.ee.db_connections.type_infer import csv_to_typed_df, json_to_typed_df, json_list_to_typed_df


def _get_csv(csv_name):
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_script_dir, "csvs", csv_name)

    # Open the file in binary mode and read its contents
    with open(file_path, "rb") as file:
        csv_bytes = file.read()

    return csv_bytes


def _get_json(json_name):
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_script_dir, "json", json_name)

    # Open the file in binary mode and read its contents
    with open(file_path, "rb") as file:
        json_bytes = file.read()

    return json_bytes


@skipIf(not EXPLORER_USER_UPLOADS_ENABLED, "User uploads not enabled")
class TestCsvToTypedDf(TestCase):

    def test_mixed_types(self):
        df = csv_to_typed_df(_get_csv("mixed.csv"))
        self.assertTrue(pd.api.types.is_object_dtype(df["Value1"]))
        self.assertTrue(pd.api.types.is_object_dtype(df["Value2"]))
        self.assertTrue(pd.api.types.is_object_dtype(df["Value3"]))

    def test_all_types(self):
        df = csv_to_typed_df(_get_csv("all_types.csv"))
        self.assertTrue(pd.api.types.is_datetime64_ns_dtype(df["Dates"]))
        self.assertTrue(pd.api.types.is_integer_dtype(df["Integers"]))
        self.assertTrue(pd.api.types.is_float_dtype(df["Floats"]))
        self.assertTrue(pd.api.types.is_object_dtype(df["Strings"]))

    def test_integer_parsing(self):
        df = csv_to_typed_df(_get_csv("integers.csv"))
        self.assertTrue(pd.api.types.is_integer_dtype(df["Integers"]))
        self.assertTrue(pd.api.types.is_integer_dtype(df["More_integers"]))

    def test_float_parsing(self):
        df = csv_to_typed_df(_get_csv("floats.csv"))
        self.assertTrue(pd.api.types.is_float_dtype(df["Floats"]))

    def test_date_parsing(self):

        # Will not handle these formats:
        # Unix Timestamp: 1706232300 (Seconds since Unix Epoch - 1970-01-01 00:00:00 UTC)
        # ISO 8601 Week Number: 2024-W04-3 (Year-WWeekNumber-Weekday)
        # Day of Year: 2024-024 (Year-DayOfYear)

        df = csv_to_typed_df(_get_csv("dates.csv"))
        self.assertTrue(pd.api.types.is_datetime64_ns_dtype(df["Dates"]))


@skipIf(not EXPLORER_USER_UPLOADS_ENABLED, "User uploads not enabled")
class TestJsonToTypedDf(TestCase):

    def test_basic_json(self):
        df = json_to_typed_df(_get_json("kings.json"))
        self.assertTrue(pd.api.types.is_object_dtype(df["Name"]))
        self.assertTrue(pd.api.types.is_object_dtype(df["Country"]))
        self.assertTrue(pd.api.types.is_integer_dtype(df["ID"]))

    def test_nested_json(self):
        df = json_to_typed_df(_get_json("github.json"))
        self.assertTrue(pd.api.types.is_object_dtype(df["subscription_url"]))
        self.assertTrue(pd.api.types.is_object_dtype(df["topics"]))
        self.assertTrue(pd.api.types.is_integer_dtype(df["size"]))
        self.assertTrue(pd.api.types.is_integer_dtype(df["owner.id"]))

    def test_json_list(self):
        df = json_list_to_typed_df(_get_json("list.json"))
        self.assertTrue(pd.api.types.is_integer_dtype(df["Item.value.M.unique_connection_count.N"]))
        self.assertTrue(pd.api.types.is_object_dtype(df["Item.instanceId.S"]))
        self.assertEqual(len(df), 5)
