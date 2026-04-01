import uuid
import os
import logging
from typing import Optional

from fastapi import UploadFile
from app.core.config import settings

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
LOCAL_UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")


class S3Service:
    """File upload — uses S3 if configured, otherwise saves locally."""

    def __init__(self):
        self._client = None

    @property
    def _s3_configured(self) -> bool:
        return bool(settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY)

    @property
    def client(self):
        if self._client is None and self._s3_configured:
            import boto3
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
        """Upload file. Uses S3 if configured, local storage otherwise."""
        if not file.filename:
            return None

        ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"File type {ext} not allowed. Accepted: {', '.join(ALLOWED_EXTENSIONS)}")

        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise ValueError(f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB")

        filename = f"{uuid.uuid4()}{ext}"

        if self._s3_configured:
            return await self._upload_s3(content, folder, filename, ext)
        else:
            return self._save_local(content, folder, filename)

    async def _upload_s3(self, content: bytes, folder: str, filename: str, ext: str) -> str:
        from botocore.exceptions import ClientError

        key = f"{folder}/{filename}"
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
            return f"https://{settings.AWS_S3_BUCKET}.s3.{settings.AWS_S3_REGION}.amazonaws.com/{key}"
        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            raise ValueError("File upload failed. Please try again.")

    def _save_local(self, content: bytes, folder: str, filename: str) -> str:
        """Save to local uploads/ directory for testing."""
        upload_dir = os.path.join(LOCAL_UPLOAD_DIR, folder)
        os.makedirs(upload_dir, exist_ok=True)

        filepath = os.path.join(upload_dir, filename)
        with open(filepath, "wb") as f:
            f.write(content)

        logger.info(f"File saved locally: {filepath}")
        return f"/uploads/{folder}/{filename}"


s3_service = S3Service()
