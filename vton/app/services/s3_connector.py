import logging
import os
from io import BytesIO

import boto3
import httpx
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class S3Connector:
    def __init__(self, r2_access_key: str, r2_secret_key: str, r2_account_id: str, bucket: str = "ft-lineone-vton"):
        self.bucket = bucket
        self.public_url = os.getenv("R2_PUBLIC_URL", "").rstrip("/")
        self.client = boto3.client(
            "s3",
            aws_access_key_id=r2_access_key,
            aws_secret_access_key=r2_secret_key,
            endpoint_url=f"https://{r2_account_id}.r2.cloudflarestorage.com"
        )

    def upload_image(
        self, image_bytes: bytes, key: str, bucket: str | None = None
    ) -> str:
        target_bucket = bucket or self.bucket
        try:
            self.client.put_object(
                Bucket=target_bucket,
                Key=key,
                Body=image_bytes,
                ContentType="image/png",
            )
            if self.public_url:
                url = f"{self.public_url}/{target_bucket}/{key}"
            else:
                url = f"/{target_bucket}/{key}"
            logger.info("Uploaded image to %s", url)
            return url
        except ClientError as exc:
            logger.error("R2 upload failed: %s", exc)
            raise

    def download_image(self, url: str) -> bytes:
        resp = httpx.get(url, follow_redirects=True, timeout=30)
        resp.raise_for_status()
        return resp.content

    def delete_image(self, key: str, bucket: str | None = None) -> bool:
        target_bucket = bucket or self.bucket
        try:
            self.client.delete_object(Bucket=target_bucket, Key=key)
            logger.info("Deleted r2://%s/%s", target_bucket, key)
            return True
        except ClientError as exc:
            logger.error("R2 delete failed: %s", exc)
            return False

    def get_presigned_url(self, key: str, expires: int = 3600) -> str:
        try:
            url = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=expires,
            )
            return url
        except ClientError as exc:
            logger.error("Failed to generate presigned URL: %s", exc)
            raise
