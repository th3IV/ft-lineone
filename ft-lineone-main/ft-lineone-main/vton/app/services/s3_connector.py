import logging
from io import BytesIO
from urllib.parse import urlparse

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class S3Connector:
    def __init__(self, bucket: str = None, region: str = None):
        self.bucket = bucket or "ft-lineone-vton"
        self.region = region or "us-east-1"
        self.client = boto3.client("s3", region_name=self.region)

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
            url = f"https://{target_bucket}.s3.{self.region}.amazonaws.com/{key}"
            logger.info("Uploaded image to %s", url)
            return url
        except ClientError as exc:
            logger.error("S3 upload failed: %s", exc)
            raise

    def download_image(self, url: str) -> bytes:
        parsed = urlparse(url)
        if parsed.netloc.endswith("amazonaws.com"):
            bucket = parsed.netloc.split(".")[0]
            key = parsed.path.lstrip("/")
            try:
                response = self.client.get_object(Bucket=bucket, Key=key)
                return response["Body"].read()
            except ClientError as exc:
                logger.error("S3 download failed: %s", exc)
                raise
        import httpx
        resp = httpx.get(url, follow_redirects=True, timeout=30)
        resp.raise_for_status()
        return resp.content

    def delete_image(self, key: str, bucket: str | None = None) -> bool:
        target_bucket = bucket or self.bucket
        try:
            self.client.delete_object(Bucket=target_bucket, Key=key)
            logger.info("Deleted s3://%s/%s", target_bucket, key)
            return True
        except ClientError as exc:
            logger.error("S3 delete failed: %s", exc)
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
