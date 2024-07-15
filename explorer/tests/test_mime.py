from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from explorer.ee.db_connections.mime import is_sqlite, is_json, is_json_list, is_csv
import io
import sqlite3
import os


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


class TestIsJsonFunction(TestCase):

    def test_is_json_with_valid_json(self):
        long_json = '{"key1": "value1", "key2": {"subkey1": "subvalue1", "subkey2": "subvalue2"}, "key3": [1, 2, 3, 4]}'  #  noqa
        json_file = SimpleUploadedFile("test.json", long_json.encode("utf-8"), content_type="application/json")
        self.assertTrue(is_json(json_file))

    def test_is_json_with_non_json_file(self):
        txt_file = SimpleUploadedFile("test.txt", b"Just some text", content_type="text/plain")
        self.assertFalse(is_json(txt_file))

    def test_is_json_with_wrong_extension(self):
        long_json = '{"key1": "value1", "key2": {"subkey1": "subvalue1", "subkey2": "subvalue2"}, "key3": [1, 2, 3, 4]}'  #  noqa
        json_file = SimpleUploadedFile("test.txt", long_json.encode("utf-8"), content_type="application/json")
        self.assertFalse(is_json(json_file))

    def test_is_json_with_empty_content_type(self):
        long_json = '{"key1": "value1", "key2": {"subkey1": "subvalue1", "subkey2": "subvalue2"}, "key3": [1, 2, 3, 4]}'  #  noqa
        json_file = SimpleUploadedFile("test.json", long_json.encode("utf-8"), content_type="")
        self.assertFalse(is_json(json_file))


class TestIsJsonListFunction(TestCase):

    def test_is_json_list_with_valid_json_lines(self):
        json_lines = b'{"key1": "value1"}\n{"key2": "value2"}\n{"key3": {"subkey1": "subvalue1"}}\n'  #  noqa
        json_file = SimpleUploadedFile("test.json", json_lines, content_type="application/json")
        self.assertTrue(is_json_list(json_file))

    def test_is_json_list_with_multiline_json(self):
        json_lines = b'{"key1":\n"value1"}\n{"key2": "value2"}\n{"key3": {"subkey1": "subvalue1"}}\n'  #  noqa
        json_file = SimpleUploadedFile("test.json", json_lines, content_type="application/json")
        self.assertFalse(is_json_list(json_file))

    def test_is_json_list_with_non_json_file(self):
        txt_file = SimpleUploadedFile("test.txt", b"Just some text", content_type="text/plain")
        self.assertFalse(is_json_list(txt_file))

    def test_is_json_list_with_invalid_json_lines(self):
        # This is actually going to *pass* the check, because it's a shallow file-type check, not a comprehensive
        # one. That's ok! This type of error will get caught later, when pandas tries to parse it
        invalid_json_lines = b'{"key1": "value1"}\nNot a JSON content\n{"key3": {"subkey1": "subvalue1"}}\n'  #  noqa
        json_file = SimpleUploadedFile("test.json", invalid_json_lines, content_type="application/json")
        self.assertTrue(is_json_list(json_file))

    def test_is_json_list_with_wrong_extension(self):
        json_lines = b'{"key1": "value1"}\n{"key2": "value2"}\n{"key3": {"subkey1": "subvalue1"}}\n'  #  noqa
        json_file = SimpleUploadedFile("test.txt", json_lines, content_type="application/json")
        self.assertFalse(is_json_list(json_file))

    def test_is_json_list_with_empty_file(self):
        json_file = SimpleUploadedFile("test.json", b"", content_type="application/json")
        self.assertFalse(is_json_list(json_file))


class IsSqliteTestCase(TestCase):
    def setUp(self):
        # Create a SQLite database in a local file and read it into a BytesIO object
        # It would be nice to do this in memory, but that is not possible.
        local_path = "local_database.db"
        try:
            os.remove(local_path)
        except Exception as e:  # noqa
            pass
        conn = sqlite3.connect(local_path)
        conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
        for i in range(5):
            conn.execute("INSERT INTO test (name) VALUES (?)", (f"name_{i}",))
        conn.commit()
        conn.close()

        # Read the local SQLite database file into a BytesIO buffer
        self.sqlite_db = io.BytesIO()
        with open(local_path, "rb") as f:
            self.sqlite_db.write(f.read())
        self.sqlite_db.seek(0)

        # Clean up the local file
        os.remove(local_path)

    def test_is_sqlite_with_valid_sqlite_file(self):
        valid_sqlite_file = SimpleUploadedFile("test.sqlite", self.sqlite_db.read(),
                                               content_type="application/x-sqlite3")
        self.assertTrue(is_sqlite(valid_sqlite_file))

    def test_is_sqlite_with_invalid_sqlite_file_content_type(self):
        self.sqlite_db.seek(0)
        invalid_content_type_file = SimpleUploadedFile("test.sqlite", self.sqlite_db.read(), content_type="text/plain")
        self.assertFalse(is_sqlite(invalid_content_type_file))

    def test_is_sqlite_with_invalid_sqlite_file_header(self):
        invalid_sqlite_header = b"Invalid header" + b"\x00" * 100
        invalid_sqlite_file = SimpleUploadedFile("test.sqlite", invalid_sqlite_header,
                                                 content_type="application/x-sqlite3")
        self.assertFalse(is_sqlite(invalid_sqlite_file))

    def test_is_sqlite_with_exception_handling(self):
        class FaultyFile:
            content_type = "application/x-sqlite3"

            def seek(self, offset):
                pass

            def read(self, num_bytes):
                raise OSError("Unable to read file")

        faulty_file = FaultyFile()
        self.assertFalse(is_sqlite(faulty_file))
