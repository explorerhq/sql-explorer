import csv
import json

# These are 'shallow' checks. They are just to understand if the upload appears valid at surface-level.
# A deeper check will happen when pandas tries to parse the file.
# This is designed to be quick, and simply assigned the right (full) parsing function to the uploaded file.


def is_csv(file):
    if file.content_type != "text/csv":
        return False
    try:
        # Check if the file content can be read as a CSV
        file.seek(0)
        sample = file.read(1024).decode("utf-8")
        csv.Sniffer().sniff(sample)
        file.seek(0)
        return True
    except csv.Error:
        return False


def is_json(file):
    if file.content_type != "application/json":
        return False
    if not file.name.lower().endswith(".json"):
        return False
    return True


def is_json_list(file):
    if not file.name.lower().endswith(".json"):
        return False
    file.seek(0)
    first_line = file.readline()
    file.seek(0)
    try:
        json.loads(first_line.decode("utf-8"))
        return True
    except ValueError:
        return False


def is_sqlite(file):
    if file.content_type not in ["application/x-sqlite3", "application/octet-stream"]:
        return False
    try:
        # Check if the file starts with the SQLite file header
        file.seek(0)
        header = file.read(16)
        file.seek(0)
        return header == b"SQLite format 3\x00"
    except Exception as e:  # noqa
        return False
