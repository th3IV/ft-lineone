"""Pure-Python image compressor for JPEG — no external dependencies.

Works by modifying JPEG quantization tables to reduce quality and file size.
Only handles JPEG images (the most common format for photos).
"""

import io
import struct
from typing import Optional


class ImageCompressor:
    """Compress JPEG images by modifying quantization tables.

    This works entirely with raw bytes — no Pillow/PIL required.
    JPEG files contain quantization tables (DQT markers) that control
    compression quality. By scaling these values up, we increase
    compression and reduce file size.

    Usage:
        compressor = ImageCompressor(max_bytes=100 * 1024)
        compressed_bytes = compressor.compress(image_bytes)
    """

    JPEG_MAGIC = b"\xff\xd8\xff"

    def __init__(
        self,
        max_bytes: int = 100 * 1024,
        initial_scale: float = 1.5,
        scale_step: float = 0.5,
        min_scale: float = 1.0,
    ):
        self.max_bytes = max_bytes
        self.initial_scale = initial_scale
        self.scale_step = scale_step
        self.min_scale = min_scale

    def compress(self, image_bytes: bytes) -> bytes:
        """Compress image bytes to fit within max_bytes.

        For JPEG: modifies quantization tables to reduce quality.
        For non-JPEG: returns as-is (frontend handles compression).

        Args:
            image_bytes: Raw image bytes.

        Returns:
            Compressed image bytes.

        Raises:
            ValueError: If image format is not supported or too small.
        """
        if len(image_bytes) < 4:
            raise ValueError("Image too small")

        if not image_bytes[:3] == self.JPEG_MAGIC:
            # Not JPEG — return as-is, frontend handles compression
            return image_bytes

        if len(image_bytes) <= self.max_bytes:
            return image_bytes

        # Try progressively stronger compression
        scale = self.initial_scale
        compressed = image_bytes

        while len(compressed) > self.max_bytes and scale >= self.min_scale:
            compressed = self._reduce_jpeg_quality(image_bytes, scale)
            scale += self.scale_step

        # If still too large, try stripping EXIF/metadata
        if len(compressed) > self.max_bytes:
            stripped = self._strip_exif(image_bytes)
            compressed = self._reduce_jpeg_quality(stripped, scale)
            while len(compressed) > self.max_bytes and scale < 5.0:
                scale += 0.5
                compressed = self._reduce_jpeg_quality(stripped, scale)

        return compressed

    def validate(self, image_bytes: bytes) -> bool:
        """Validate that bytes represent a supported image format."""
        if len(image_bytes) < 4:
            return False
        header = image_bytes[:4]
        if header[:3] == self.JPEG_MAGIC:
            return True
        if header == b"\x89PNG":
            return True
        if header == b"RIFF" and image_bytes[8:12] == b"WEBP":
            return True
        return False

    def _reduce_jpeg_quality(self, jpeg_bytes: bytes, scale: float) -> bytes:
        """Reduce JPEG quality by scaling quantization table values.

        Finds DQT (Define Quantization Table) markers and multiplies
        all quantization coefficients by the scale factor.
        """
        result = io.BytesIO()
        i = 0
        length = len(jpeg_bytes)

        while i < length - 1:
            # Look for marker
            if jpeg_bytes[i] != 0xFF:
                result.write(bytes([jpeg_bytes[i]]))
                i += 1
                continue

            marker = jpeg_bytes[i + 1]

            # SOI and EOI markers have no length
            if marker in (0xD8, 0xD9):
                result.write(bytes([0xFF, marker]))
                i += 2
                continue

            # SOS marker — stop processing, rest is compressed data
            if marker == 0xDA:
                result.write(jpeg_bytes[i:])
                break

            # Read segment length
            if i + 3 >= length:
                result.write(jpeg_bytes[i:])
                break

            seg_len = struct.unpack(">H", jpeg_bytes[i + 2 : i + 4])[0]

            if marker == 0xDB:
                # DQT — Define Quantization Table
                modified = self._scale_dqt(jpeg_bytes[i : i + 2 + seg_len], scale)
                result.write(modified)
            else:
                # Copy segment as-is
                result.write(jpeg_bytes[i : i + 2 + seg_len])

            i += 2 + seg_len

        return result.getvalue()

    def _scale_dqt(self, segment: bytes, scale: float) -> bytes:
        """Scale quantization table values in a DQT segment."""
        buf = bytearray(segment)
        # DQT header: FF DB + 2-byte length
        # Then for each table: 1 byte (precision<<4|table_id), then 64 values
        offset = 4  # Skip marker + length
        while offset < len(buf):
            if offset >= len(buf):
                break
            info_byte = buf[offset]
            offset += 1
            precision = (info_byte >> 4) & 0x0F  # 0 = 8-bit, 1 = 16-bit
            table_size = 64 if precision == 0 else 128

            for j in range(table_size):
                if offset + j >= len(buf):
                    break
                val = buf[offset + j]
                if val > 0:
                    new_val = min(255, int(val * scale))
                    buf[offset + j] = max(1, new_val)

            offset += table_size

        return bytes(buf)

    def _strip_exif(self, jpeg_bytes: bytes) -> bytes:
        """Strip EXIF and other metadata from JPEG to reduce size."""
        result = io.BytesIO()
        i = 0
        length = len(jpeg_bytes)

        # Write SOI
        result.write(jpeg_bytes[:2])
        i = 2

        while i < length - 1:
            if jpeg_bytes[i] != 0xFF:
                i += 1
                continue

            marker = jpeg_bytes[i + 1]

            if marker == 0xD9:
                # EOI — end
                result.write(bytes([0xFF, 0xD9]))
                break

            if marker == 0xDA:
                # SOS — rest is compressed data
                result.write(jpeg_bytes[i:])
                break

            if i + 3 >= length:
                result.write(jpeg_bytes[i:])
                break

            seg_len = struct.unpack(">H", jpeg_bytes[i + 2 : i + 4])[0]

            # Skip EXIF (0xE1), ICC (0xE2), and other APP markers
            # Keep APP0 (JFIF) as it's useful
            if marker in (0xE0,):
                result.write(jpeg_bytes[i : i + 2 + seg_len])
            elif marker not in (0xE1, 0xE2, 0xE3, 0xE4, 0xE5, 0xE6, 0xE7, 0xE8, 0xE9, 0xEA):
                result.write(jpeg_bytes[i : i + 2 + seg_len])

            i += 2 + seg_len

        return result.getvalue()
