from django.test import TestCase
from unittest import skipIf
from explorer.app_settings import EXPLORER_USER_UPLOADS_ENABLED
if EXPLORER_USER_UPLOADS_ENABLED:
    import pandas as pd
import os
import sqlite3
from django.db import DatabaseError
from explorer.models import DatabaseConnection
from unittest.mock import patch, MagicMock
from explorer.ee.db_connections.utils import (
    pandas_to_sqlite
)


@skipIf(not EXPLORER_USER_UPLOADS_ENABLED, "User uploads not enabled")
class TestSQLiteConnection(TestCase):

    @patch("explorer.utils.get_s3_bucket")
    def test_get_sqlite_for_connection_downloads_file_if_not_exists(self, mock_get_s3_bucket):
        mock_s3 = MagicMock()
        mock_get_s3_bucket.return_value = mock_s3

        conn = DatabaseConnection(
            name="test_db.db",
            host="s3_bucket/test_db.db",
            engine=DatabaseConnection.SQLITE
        )
        conn.delete_local_sqlite()

        local_name = conn.local_name

        conn.as_django_connection()

        mock_s3.download_file.assert_called_once_with("s3_bucket/test_db.db", local_name)

    @patch("explorer.utils.get_s3_bucket")
    def test_get_sqlite_for_connection_skips_download_if_exists(self, mock_get_s3_bucket):
        mock_s3 = MagicMock()
        mock_get_s3_bucket.return_value = mock_s3

        conn = DatabaseConnection(
            name="test_db.db",
            host="s3_bucket/test_db.db",
            engine=DatabaseConnection.SQLITE
        )
        conn.delete_local_sqlite()

        local_name = conn.local_name

        with open(local_name, "wb") as file:
            file.write(b"\x00" * 10)

        conn.update_fingerprint()

        conn.as_django_connection()

        mock_s3.download_file.assert_not_called()

        os.remove(local_name)


class TestDjangoStyleConnection(TestCase):

    @patch("explorer.ee.db_connections.models.load_backend")
    def test_create_django_style_connection_with_extras(self, mock_load_backend):
        conn = DatabaseConnection(
            name="test_db",
            alias="test_db",
            engine="django.db.backends.postgresql",
            extras='{"sslmode": "require", "connect_timeout": 10}'
        )

        mock_backend = MagicMock()
        mock_load_backend.return_value = mock_backend

        conn.as_django_connection()

        mock_load_backend.assert_called_once_with("django.db.backends.postgresql")
        mock_backend.DatabaseWrapper.assert_called_once()
        args, kwargs = mock_backend.DatabaseWrapper.call_args
        self.assertEqual(args[0]["sslmode"], "require")
        self.assertEqual(args[0]["connect_timeout"], 10)


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
        db_buffer = pandas_to_sqlite(df, "data", "test_pandas_to_sqlite.db")

        # Write the buffer to a temporary file to simulate reading it back
        temp_db_path = "temp_test_database.db"
        with open(temp_db_path, "wb") as f:
            f.write(db_buffer.getbuffer())

        # Connect to the SQLite database and verify its content
        con = sqlite3.connect(temp_db_path)
        try:
            cursor = con.cursor()
            cursor.execute("SELECT * FROM data")  # noqa
            rows = cursor.fetchall()

            # Verify the content of the SQLite database
            self.assertEqual(len(rows), 3)
            self.assertEqual(rows[0], (1, "A"))
            self.assertEqual(rows[1], (2, "B"))
            self.assertEqual(rows[2], (3, "C"))
        finally:
            con.close()
            os.remove(temp_db_path)

    def test_cant_create_connection_for_unregistered_django_alias(self):
        conn = DatabaseConnection(alias="not_registered", engine=DatabaseConnection.DJANGO)
        conn.save()
        self.assertRaises(DatabaseError, conn.as_django_connection)
