from minio import Minio
from minio.error import S3Error
from typing import BinaryIO
from datetime import timedelta

from app.core.config import settings
from app.core.logging import logger


class StorageService:
    """MinIO存储服务"""
    
    def __init__(self):
        self.client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self._ensure_bucket()
    
    def _ensure_bucket(self):
        """确保Bucket存在"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"Bucket check error: {e}")
            raise
    
    async def upload_file(
        self,
        file_data: BinaryIO,
        object_name: str,
        content_type: str = "application/octet-stream",
        file_size: int = -1
    ) -> str:
        """上传文件"""
        try:
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=file_data,
                length=file_size,
                content_type=content_type,
                part_size=10 * 1024 * 1024
            )
            logger.info(f"Uploaded file: {object_name}")
            return object_name
        except S3Error as e:
            logger.error(f"Upload failed: {e}")
            raise Exception(f"Upload failed: {e}")
    
    def get_file_url(self, object_name: str, expires: int = 3600) -> str:
        """获取文件预签名URL"""
        try:
            url = self.client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                expires=timedelta(seconds=expires)
            )
            return url.replace(
                f"http://{settings.MINIO_ENDPOINT}",
                "/api/v1/files"
            )
        except S3Error:
            return ""
    
    def delete_file(self, object_name: str) -> bool:
        """删除文件"""
        try:
            self.client.remove_object(self.bucket_name, object_name)
            logger.info(f"Deleted file: {object_name}")
            return True
        except S3Error as e:
            logger.error(f"Delete failed: {e}")
            return False
    
    def get_file_stream(self, object_name: str):
        """获取文件流"""
        try:
            response = self.client.get_object(self.bucket_name, object_name)
            return response
        except S3Error as e:
            logger.error(f"Get file failed: {e}")
            raise
