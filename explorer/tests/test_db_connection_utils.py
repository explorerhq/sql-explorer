from django.test import TestCase
from unittest import skipIf
from django.core.files.uploadedfile import SimpleUploadedFile
from explorer.app_settings import EXPLORER_USER_UPLOADS_ENABLED
if EXPLORER_USER_UPLOADS_ENABLED:
    import pandas as pd
import os
import sqlite3
from explorer.models import DatabaseConnection
from unittest.mock import patch, MagicMock
from explorer.ee.db_connections.utils import (
    get_sqlite_for_connection,
    create_django_style_connection,
    pandas_to_sqlite,
    is_csv,
    csv_to_typed_df
)


def _get_csv(csv_name):
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_script_dir, "csvs", csv_name)

    # Open the file in binary mode and read its contents
    with open(file_path, "rb") as file:
        csv_bytes = file.read()

    return csv_bytes


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
        print(df["Integers"].dtype)
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
class TestSQLiteConnection(TestCase):

    @patch("explorer.utils.get_s3_bucket")
    @patch("os.path.exists")
    @patch("os.getcwd")
    def test_get_sqlite_for_connection_downloads_file_if_not_exists(self, mock_getcwd, mock_path_exists,
                                                                    mock_get_s3_bucket):
        mock_getcwd.return_value = "/tmp"
        mock_path_exists.return_value = False
        mock_s3 = MagicMock()
        mock_get_s3_bucket.return_value = mock_s3

        mock_explorer_connection = MagicMock()
        mock_explorer_connection.name = "test_db"
        mock_explorer_connection.host = "s3_bucket/test_db"
        mock_explorer_connection.local_name = "/tmp/user_dbs/test_db"

        result = get_sqlite_for_connection(mock_explorer_connection)

        mock_s3.download_file.assert_called_once_with("s3_bucket/test_db", "/tmp/user_dbs/test_db")
        self.assertIsNone(result.host)
        self.assertEqual(result.name, "/tmp/user_dbs/test_db")

    @patch("explorer.utils.get_s3_bucket")
    @patch("os.path.exists")
    @patch("os.getcwd")
    def test_get_sqlite_for_connection_skips_download_if_exists(self, mock_getcwd, mock_path_exists,
                                                                mock_get_s3_bucket):
        mock_getcwd.return_value = "/tmp"
        mock_path_exists.return_value = True
        mock_s3 = MagicMock()
        mock_get_s3_bucket.return_value = mock_s3

        mock_explorer_connection = MagicMock()
        mock_explorer_connection.name = "test_db"
        mock_explorer_connection.host = "s3_bucket/test_db"
        mock_explorer_connection.local_name = "/tmp/user_dbs/test_db"

        result = get_sqlite_for_connection(mock_explorer_connection)

        mock_s3.download_file.assert_not_called()
        self.assertIsNone(result.host)
        self.assertEqual(result.name, "/tmp/user_dbs/test_db")


class TestDjangoStyleConnection(TestCase):

    @patch("explorer.ee.db_connections.utils.get_sqlite_for_connection")
    @patch("explorer.ee.db_connections.utils.load_backend")
    def test_create_django_style_connection_sqlite(self, mock_load_backend, mock_get_sqlite_for_connection):
        mock_explorer_connection = MagicMock()
        mock_explorer_connection.engine = DatabaseConnection.SQLITE
        mock_explorer_connection.host = "s3_bucket/test_db"
        mock_get_sqlite_for_connection.return_value = mock_explorer_connection

        mock_backend = MagicMock()
        mock_load_backend.return_value = mock_backend

        create_django_style_connection(mock_explorer_connection)

        mock_get_sqlite_for_connection.assert_called_once_with(mock_explorer_connection)
        mock_backend.DatabaseWrapper.assert_called_once()

    @patch("explorer.ee.db_connections.utils.load_backend")
    def test_create_django_style_connection_non_sqlite(self, mock_load_backend):
        mock_explorer_connection = MagicMock()
        mock_explorer_connection.is_upload = False
        mock_explorer_connection.engine = "django.db.backends.postgresql"

        mock_backend = MagicMock()
        mock_load_backend.return_value = mock_backend

        create_django_style_connection(mock_explorer_connection)

        mock_load_backend.assert_called_once_with("django.db.backends.postgresql")
        mock_backend.DatabaseWrapper.assert_called_once()


@skipIf(not EXPLORER_USER_UPLOADS_ENABLED, "User uploads not enabled")
class TestPandasToSQLite(TestCase):

    def test_pandas_to_sqlite(self):
        # Create a sample DataFrame
        data = {
            "column1": [1, 2, 3],
            "column2": ["A", "B", "C"]
        }
        df = pd.DataFrame(data)

        # Convert the DataFrame to SQLite and get the BytesIO buffer
        db_buffer = pandas_to_sqlite(df)

        # Write the buffer to a temporary file to simulate reading it back
        temp_db_path = "temp_test_database.db"
        with open(temp_db_path, "wb") as f:
            f.write(db_buffer.getbuffer())

        # Connect to the SQLite database and verify its content
        con = sqlite3.connect(temp_db_path)
        try:
            cursor = con.cursor()
            cursor.execute("SELECT * FROM data")
            rows = cursor.fetchall()

            # Verify the content of the SQLite database
            self.assertEqual(len(rows), 3)
            self.assertEqual(rows[0], (1, "A"))
            self.assertEqual(rows[1], (2, "B"))
            self.assertEqual(rows[2], (3, "C"))
        finally:
            con.close()
            os.remove(temp_db_path)


class TestIsCsvFunction(TestCase):

    def test_is_csv_with_csv_file(self):
        # Create a SimpleUploadedFile with content_type set to "text/csv"
        csv_file = SimpleUploadedFile("test.csv", b"column1,column2\n1,A\n2,B", content_type="text/csv")
        self.assertTrue(is_csv(csv_file))

    def test_is_csv_with_non_csv_file(self):
        # Create a SimpleUploadedFile with content_type set to "text/plain"
        txt_file = SimpleUploadedFile("test.txt", b"Just some text", content_type="text/plain")
        self.assertFalse(is_csv(txt_file))

    def test_is_csv_with_empty_content_type(self):
        # Create a SimpleUploadedFile with an empty content_type
        empty_file = SimpleUploadedFile("test.csv", b"column1,column2\n1,A\n2,B", content_type="")
        self.assertFalse(is_csv(empty_file))
