import os
from io import BytesIO
from minio import Minio
from minio.error import S3Error
from loguru import logger

class MinioStorageClient:
    """
    MinIO SDK wrapper managing bucket lifecycle, uploads, and media retrieval.
    Credentials and endpoint are loaded strictly from environment variables:
    - MINIO_ENDPOINT_URL
    - MINIO_ACCESS_KEY
    - MINIO_SECRET_KEY
    """
    def __init__(self):
        endpoint_raw = os.getenv('MINIO_ENDPOINT_URL', 'localhost:9000')
        secure = False

        if endpoint_raw.startswith('https://'):
            self.endpoint = endpoint_raw[len('https://'):]
            secure = True
        elif endpoint_raw.startswith('http://'):
            self.endpoint = endpoint_raw[len('http://'):]
            secure = False
        else:
            self.endpoint = endpoint_raw

        self.access_key = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
        self.secret_key = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
        self.bucket_name = os.getenv('MINIO_BUCKET_NAME', 'dicoevent')

        self.client = Minio(
            endpoint=self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=secure,
        )
        self._bucket_checked = False

    def _ensure_bucket(self):
        if self._bucket_checked:
            return
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created MinIO bucket '{self.bucket_name}'")
            self._bucket_checked = True
        except Exception as e:
            logger.warning(f"Could not connect or check MinIO bucket '{self.bucket_name}': {e}")

    def upload_file(self, file_obj, object_name: str, content_type: str = 'application/octet-stream') -> str:
        """
        Uploads a file-like object to MinIO and returns the object name.
        """
        try:
            # If bucket didn't exist initially, try ensuring again
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)

            file_size = getattr(file_obj, 'size', None)
            if file_size is None:
                # Seek end to get size
                file_obj.seek(0, os.SEEK_END)
                file_size = file_obj.tell()
                file_obj.seek(0)

            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=file_obj,
                length=file_size,
                content_type=content_type,
            )
            logger.info(f"Successfully uploaded {object_name} ({file_size} bytes) to MinIO bucket {self.bucket_name}")
            return object_name
        except Exception as e:
            logger.error(f"Failed to upload {object_name} to MinIO: {e}")
            raise e

    def get_object(self, object_name: str):
        """
        Retrieves object stream from MinIO.
        """
        return self.client.get_object(self.bucket_name, object_name)

    def get_presigned_url(self, object_name: str, expires_seconds: int = 3600) -> str:
        """
        Generates a presigned URL to view/download the object.
        """
        try:
            from datetime import timedelta
            return self.client.presigned_get_object(
                self.bucket_name,
                object_name,
                expires=timedelta(seconds=expires_seconds)
            )
        except Exception as e:
            logger.error(f"Error generating presigned URL for {object_name}: {e}")
            return f"http://{self.endpoint}/{self.bucket_name}/{object_name}"

# Global instance for reuse
minio_client = MinioStorageClient()
