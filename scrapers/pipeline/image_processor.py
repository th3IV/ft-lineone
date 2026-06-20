from io import BytesIO

from PIL import Image, ImageDraw, ImageFont


class ImageProcessor:

    def process_image(self, image_bytes: bytes, product_id: str) -> bytes:
        image = Image.open(BytesIO(image_bytes))
        image = self._resize_image(image, 800, 800)
        image = self._add_watermark(image, product_id)
        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=85)
        return buffer.getvalue()

    def upload_to_s3(self, image_bytes: bytes, key: str) -> str:
        import boto3
        import os
        r2_account_id = os.getenv("R2_ACCOUNT_ID")
        r2_access_key = os.getenv("R2_ACCESS_KEY_ID")
        r2_secret_key = os.getenv("R2_SECRET_ACCESS_KEY")
        bucket = os.getenv("R2_BUCKET", "ft-lineone-images")
        
        s3 = boto3.client(
            "s3",
            aws_access_key_id=r2_access_key,
            aws_secret_access_key=r2_secret_key,
            endpoint_url=f"https://{r2_account_id}.r2.cloudflarestorage.com"
        )
        s3.put_object(Bucket=bucket, Key=key, Body=image_bytes)
        return f"{os.getenv('R2_PUBLIC_URL')}/{bucket}/{key}"

    def generate_thumbnail(self, image_bytes: bytes) -> bytes:
        image = Image.open(BytesIO(image_bytes))
        image.thumbnail((150, 150))
        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=70)
        return buffer.getvalue()

    def validate_image(self, image_bytes: bytes) -> bool:
        try:
            image = Image.open(BytesIO(image_bytes))
            image.verify()
            return True
        except Exception:
            return False

    def _resize_image(self, image: Image.Image, width: int, height: int) -> Image.Image:
        image.thumbnail((width, height), Image.LANCZOS)
        return image

    def _add_watermark(self, image: Image.Image, product_id: str) -> Image.Image:
        watermark_layer = Image.new("RGBA", image.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(watermark_layer)
        try:
            font = ImageFont.truetype("arial.ttf", 36)
        except OSError:
            font = ImageFont.load_default()
        text = f"FT-L1 {product_id}"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = image.width - text_width - 10
        y = image.height - text_height - 10
        draw.text((x, y), text, font=font, fill=(255, 255, 255, 128))
        return Image.alpha_composite(image.convert("RGBA"), watermark_layer).convert("RGB")
