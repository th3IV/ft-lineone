import os
import uuid
from pathlib import Path

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"


class LocalStorage:
    def __init__(self, base_dir: str | None = None):
        self.base_dir = Path(base_dir) if base_dir else UPLOAD_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_image(self, data: bytes, filename: str | None = None) -> str:
        if not filename:
            filename = f"{uuid.uuid4()}.png"
        dest = self.base_dir / filename
        dest.write_bytes(data)
        return filename

    def get_path(self, filename: str) -> str:
        return str(self.base_dir / filename)

    def get_url(self, filename: str) -> str:
        return f"/uploads/{filename}"

    def delete(self, filename: str) -> bool:
        path = self.base_dir / filename
        if path.exists():
            path.unlink()
            return True
        return False
