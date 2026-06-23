import io
import logging
from io import BytesIO
from PIL import Image, ImageFilter

logger = logging.getLogger(__name__)


class ImageProcessor:
    @staticmethod
    def resize_image(image: Image.Image, max_size: tuple[int, int]) -> Image.Image:
        image = image.convert("RGB")
        image.thumbnail(max_size, Image.LANCZOS)
        return image

    @staticmethod
    def remove_background(image: Image.Image) -> Image.Image:
        try:
            from rembg import remove
            result = remove(image)
            return result
        except ImportError:
            logger.warning("rembg not installed. Using fallback background removal.")
            return ImageProcessor._remove_background_fallback(image)

    @staticmethod
    def _remove_background_fallback(image: Image.Image) -> Image.Image:
        image = image.convert("RGBA")
        gray = image.convert("L")
        threshold = 240
        mask = gray.point(lambda p: 0 if p > threshold else 255)
        result = Image.new("RGBA", image.size, (0, 0, 0, 0))
        result.paste(image, mask=mask)
        return result

    @staticmethod
    def align_pose(
        user_image: Image.Image, clothing_image: Image.Image
    ) -> tuple[Image.Image, Image.Image]:
        user_image = ImageProcessor.resize_image(user_image, (512, 512))
        clothing_image = ImageProcessor.resize_image(clothing_image, (512, 512))
        return user_image, clothing_image

    @staticmethod
    def composite_result(
        user: Image.Image, clothing: Image.Image, mask: Image.Image
    ) -> Image.Image:
        user = user.convert("RGBA")
        clothing = clothing.convert("RGBA")
        mask = mask.convert("L").resize(user.size, Image.LANCZOS)
        composite = Image.composite(clothing, user, mask)
        return composite.convert("RGB")

    @staticmethod
    def encode_image(image: Image.Image, format: str = "PNG") -> bytes:
        buffer = BytesIO()
        image.save(buffer, format=format)
        return buffer.getvalue()
