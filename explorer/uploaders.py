import io

from django.utils.module_loading import import_string

from explorer import app_settings


def get_uploader_class(uploader):
    class_str = dict(getattr(app_settings, 'EXPLORER_DATA_UPLOADERS'))[uploader]
    return import_string(class_str)

class BaseUploader:

    def prepare_file(self, data):
        csv_file_io = data.get_file_output()
        csv_file_io.seek(0)
        csv_data = csv_file_io.read()
        bio = io.BytesIO(bytes(csv_data, 'utf-8'))
        return bio

    def upload(self):
        raise NotImplementedError

class FileUploader(BaseUploader):
    def upload(self, key, data):
        from zipfile import ZipFile
        import os
        import shutil
        full_filename = os.path.join(app_settings.SNAPSHOTS_UPLOAD_DIR, f"{key}.zip")
        download_url = os.path.join(app_settings.SNAPSHOTS_DOWNLOAD_DIR, f"{key}.zip")
        with ZipFile(full_filename, 'w') as zfh:
            zfh.writestr(f"{key}.csv", self.prepare_file(data).getvalue())
        return download_url

class S3Uploader(BaseUploader):
    def get_s3_bucket(self):
        import boto3
        kwargs = {
            'aws_access_key_id': app_settings.S3_ACCESS_KEY,
            'aws_secret_access_key': app_settings.S3_SECRET_KEY,
            'region_name': app_settings.S3_REGION
        }
        if app_settings.S3_ENDPOINT_URL:
            kwargs['endpoint_url'] = app_settings.S3_ENDPOINT_URL
        s3 = boto3.resource('s3', **kwargs)
        return s3.Bucket(name=app_settings.S3_BUCKET)

    def s3_url(self, bucket, key):
        url = bucket.meta.client.generate_presigned_url(
            ClientMethod='get_object',
            Params={'Bucket': app_settings.S3_BUCKET, 'Key': key},
            ExpiresIn=app_settings.S3_LINK_EXPIRATION)
        return url

    def upload(self, key, data):
        bucket = self.get_s3_bucket()
        bucket.upload_fileobj(self.prepare_file(data), key, ExtraArgs={'ContentType': "text/csv"})
        return self.s3_url(bucket, key)
