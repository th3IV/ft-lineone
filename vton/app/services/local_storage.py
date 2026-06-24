import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"


class LocalStorage:
    def __init__(self):
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    def save_image(self, image_bytes: bytes, key: str) -> str:
        filepath = UPLOAD_DIR / key
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_bytes(image_bytes)
        url = f"http://localhost:8001/uploads/{key}"
        logger.info("Saved local image to %s", url)
        return url

    def get_local_path(self, key: str) -> str:
        return str(UPLOAD_DIR / key)

    def delete_image(self, key: str) -> bool:
        filepath = UPLOAD_DIR / key
        if filepath.exists():
            filepath.unlink()
            logger.info("Deleted local image %s", key)
            return True
        return False
