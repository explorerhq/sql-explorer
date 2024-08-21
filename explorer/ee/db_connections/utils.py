import os

import hashlib
import sqlite3
import io


def default_db_connection():
    from explorer.ee.db_connections.models import DatabaseConnection
    return DatabaseConnection.objects.default()


def default_db_connection_id():
    return default_db_connection().id


# Uploading the same filename twice (from the same user) will overwrite the 'old' DB on S3
def upload_sqlite(db_bytes, path):
    from explorer.utils import get_s3_bucket
    bucket = get_s3_bucket()
    bucket.put_object(Key=path, Body=db_bytes, ServerSideEncryption="AES256")


# Aliases have the user_id appended to them so that if two users upload files with the same name
# they don't step on one another. Without this, the *files* would get uploaded separately (because
# the DBs go into user-specific folders on s3), but the *aliases* would be the same. So one user
# could (innocently) upload a file with the same name, and any existing queries would be suddenly pointing
# to this new database connection. Oops!
def create_connection_for_uploaded_sqlite(filename, s3_path):
    from explorer.ee.db_connections.models import DatabaseConnection
    return DatabaseConnection.objects.create(
        alias=filename,
        engine=DatabaseConnection.SQLITE,
        name=filename,
        host=s3_path,
    )


def user_dbs_local_dir():
    d = os.path.normpath(os.path.join(os.getcwd(), "user_dbs"))
    if not os.path.exists(d):
        os.makedirs(d)
    return d


def uploaded_db_local_path(name):
    return os.path.join(user_dbs_local_dir(), name)


def sqlite_to_bytesio(local_path):
    # Write the file to disk. It'll be uploaded to s3, and left here locally for querying
    db_file = io.BytesIO()
    with open(local_path, "rb") as f:
        db_file.write(f.read())
    db_file.seek(0)
    return db_file


def pandas_to_sqlite(df, table_name, local_path):
    # Write the DataFrame to a local SQLite database and return it as a BytesIO object.
    # This intentionally leaves the sqlite db on the local disk so that it is ready to go for
    # querying immediately after the connection has been created. Removing it would also be OK, since
    # the system knows to re-download it if it's not available, but this saves an extra download from S3.
    conn = sqlite3.connect(local_path)

    try:
        df.to_sql(table_name, conn, if_exists="replace", index=False)
    finally:
        conn.commit()
        conn.close()

    return sqlite_to_bytesio(local_path)


def quick_hash(file_path, num_samples=10, sample_size=1024):
    hasher = hashlib.sha256()
    file_size = os.path.getsize(file_path)

    if file_size == 0:
        return hasher.hexdigest()

    sample_interval = file_size // num_samples
    with open(file_path, "rb") as f:
        for i in range(num_samples):
            f.seek(i * sample_interval)
            sample_data = f.read(sample_size)
            if not sample_data:
                break
            hasher.update(sample_data)

    return hasher.hexdigest()
