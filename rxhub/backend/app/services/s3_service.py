import uuid
import logging
from typing import Optional

import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile

from app.core.config import settings

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


class S3Service:
    """File upload to AWS S3."""

    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = boto3.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION,
            )
        return self._client

    async def upload_file(
        self, file: UploadFile, folder: str = "prescriptions"
    ) -> Optional[str]:
        """Upload file to S3, return public URL."""
        if not file.filename:
            return None

        ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"File type {ext} not allowed. Accepted: {', '.join(ALLOWED_EXTENSIONS)}")

        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise ValueError(f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB")

        key = f"{folder}/{uuid.uuid4()}{ext}"

        content_type_map = {
            ".pdf": "application/pdf",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
        }

        try:
            self.client.put_object(
                Bucket=settings.AWS_S3_BUCKET,
                Key=key,
                Body=content,
                ContentType=content_type_map.get(ext, "application/octet-stream"),
            )
            url = f"https://{settings.AWS_S3_BUCKET}.s3.{settings.AWS_S3_REGION}.amazonaws.com/{key}"
            return url
        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            raise ValueError("File upload failed. Please try again.")


s3_service = S3Service()
