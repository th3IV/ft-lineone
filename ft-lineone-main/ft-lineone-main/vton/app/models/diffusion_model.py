import logging
from io import BytesIO
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)


class DiffusionModel:
    def __init__(self, model_name: str = "stable-diffusion-vton"):
        self.model_name = model_name
        self.pipeline = None
        self.device = self._detect_device()
        self._loaded = False

    def _detect_device(self) -> str:
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return "mps"
        except ImportError:
            pass
        return "cpu"

    def load_model(self):
        if self._loaded:
            return
        try:
            import torch
            from diffusers import StableDiffusionPipeline
            self.pipeline = StableDiffusionPipeline.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            )
            self.pipeline.to(self.device)
            self.pipeline.enable_attention_slicing()
            self._loaded = True
            logger.info("Diffusion model loaded on %s", self.device)
        except Exception as exc:
            logger.warning("Could not load real diffusion model: %s. Using mock fallback.", exc)
            self._loaded = True

    def preprocess_user_image(self, image: Image.Image) -> Image.Image:
        image = image.convert("RGB")
        max_dim = 768
        ratio = max_dim / max(image.size)
        if ratio < 1:
            new_size = (int(image.width * ratio), int(image.height * ratio))
            image = image.resize(new_size, Image.LANCZOS)
        return image

    def preprocess_clothing(self, image: Image.Image) -> Image.Image:
        image = image.convert("RGB")
        max_dim = 768
        ratio = max_dim / max(image.size)
        if ratio < 1:
            new_size = (int(image.width * ratio), int(image.height * ratio))
            image = image.resize(new_size, Image.LANCZOS)
        return image

    def generate_try_on(
        self,
        user_image: Image.Image,
        clothing_image: Image.Image,
        pose_keypoints: dict | None = None,
    ) -> Image.Image:
        self.load_model()
        user_image = self.preprocess_user_image(user_image)
        clothing_image = self.preprocess_clothing(clothing_image)

        if self.pipeline is not None and self._loaded:
            try:
                prompt = "a person wearing the given clothing item, photorealistic, high quality"
                result = self.pipeline(
                    prompt=prompt,
                    image=user_image,
                    num_inference_steps=30,
                    guidance_scale=7.5,
                ).images[0]
                return self.postprocess_result(result)
            except Exception as exc:
                logger.error("Diffusion inference failed: %s. Falling back to composite.", exc)

        return self._mock_generate(user_image, clothing_image)

    def _mock_generate(self, user: Image.Image, clothing: Image.Image) -> Image.Image:
        canvas_size = (max(user.width, clothing.width), user.height + clothing.height + 20)
        canvas = Image.new("RGB", canvas_size, (255, 255, 255))
        canvas.paste(user, (0, 0))
        canvas.paste(clothing, (0, user.height + 20))
        return canvas

    def postprocess_result(self, image: Image.Image) -> Image.Image:
        image = image.convert("RGB")
        return image

    def unload_model(self):
        self.pipeline = None
        self._loaded = False
        import gc
        gc.collect()
        try:
            import torch
            torch.cuda.empty_cache()
        except (ImportError, AttributeError):
            pass
