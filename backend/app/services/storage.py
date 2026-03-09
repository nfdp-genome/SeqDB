import hashlib
from datetime import timedelta

from minio import Minio

from app.config import settings


class StorageService:
    BUCKET_RAW = "nfdp-raw"
    BUCKET_QC = "nfdp-qc"
    BUCKET_PROCESSED = "nfdp-processed"
    BUCKET_SNPCHIP = "nfdp-snpchip"
    BUCKET_STAGING = "nfdp-staging"

    ALL_BUCKETS = [BUCKET_RAW, BUCKET_QC, BUCKET_PROCESSED, BUCKET_SNPCHIP, BUCKET_STAGING]

    def __init__(self):
        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )

    def ensure_buckets(self):
        for bucket in self.ALL_BUCKETS:
            if not self.client.bucket_exists(bucket):
                self.client.make_bucket(bucket)

    @staticmethod
    def build_object_path(
        project_acc: str, sample_acc: str, run_acc: str, filename: str
    ) -> str:
        return f"{project_acc}/{sample_acc}/{run_acc}/{filename}"

    def generate_presigned_upload_url(
        self, bucket: str, object_path: str, expires_hours: int = 24
    ) -> str:
        return self.client.presigned_put_object(
            bucket, object_path, expires=timedelta(hours=expires_hours)
        )

    def generate_presigned_download_url(
        self, bucket: str, object_path: str, expires_hours: int = 24
    ) -> str:
        return self.client.presigned_get_object(
            bucket, object_path, expires=timedelta(hours=expires_hours)
        )

    def get_object_stat(self, bucket: str, object_path: str):
        return self.client.stat_object(bucket, object_path)

    def compute_object_md5(self, bucket: str, object_path: str) -> str:
        """Download an object from MinIO and compute its MD5 hex digest."""
        response = self.client.get_object(bucket, object_path)
        try:
            md5 = hashlib.md5()
            for chunk in iter(lambda: response.read(8192), b""):
                md5.update(chunk)
            return md5.hexdigest()
        finally:
            response.close()
            response.release_conn()
