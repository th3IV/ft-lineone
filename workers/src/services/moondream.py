"""Moondream vision model service for quick image pre-validation."""

import json
import asyncio
import js
from pyodide.ffi import to_js as _to_js
from js import Object


def to_js(obj):
    return _to_js(obj, dict_converter=Object.fromEntries)


MOONDREAM_MODEL = "@cf/moondream/moondream3.1-9B-A2B"


async def _fetch_with_timeout(url, options, timeout_ms=15000):
    """Wrapper around js.fetch with AbortController timeout."""
    controller = js.AbortController.new()
    signal = controller.signal
    opts = to_js({**options, "signal": signal})
    timer = js.setTimeout(lambda: controller.abort(), timeout_ms)
    try:
        resp = await js.fetch(url, opts)
        js.clearTimeout(timer)
        return resp
    except Exception as e:
        js.clearTimeout(timer)
        if "abort" in str(e).lower() or "timeout" in str(e).lower():
            raise Exception(f"Request timeout after {timeout_ms}ms: {url}")
        raise


class MoondreamService:
    """Moondream 3.1 service for quick vision tasks (human body detection)."""

    def __init__(self, env):
        self.ai = env.AI

    async def detect_human_body(self, image_url: str) -> dict:
        """
        Quick check if image contains a human body suitable for VTON.
        
        Returns:
            {"has_body": bool, "confidence": float, "details": str}
        """
        try:
            # Use Moondream's VQA capability to check for human body
            result = await self.ai.run(
                MOONDREAM_MODEL,
                {
                    "image": image_url,
                    "question": "Is there a person with a visible human body in this image? Answer yes or no.",
                },
            )
            
            response_text = str(result.get("answer", "")).lower().strip()
            has_body = "yes" in response_text
            
            return {
                "has_body": has_body,
                "confidence": 0.9 if has_body else 0.7,
                "details": response_text,
            }
            
        except Exception as e:
            # On error, allow the request to proceed (fail-open for UX)
            print(json.dumps({
                "event": "moondream_error",
                "error": str(e),
                "image_url": image_url[:100],
            }))
            return {
                "has_body": True,  # Fail open - don't block user
                "confidence": 0.0,
                "details": f"Pre-check failed: {str(e)[:100]}",
            }

    async def detect_garment_type(self, image_url: str) -> str:
        """Detect garment category from image."""
        try:
            result = await self.ai.run(
                MOONDREAM_MODEL,
                {
                    "image": image_url,
                    "question": "What type of clothing is this? Answer with one word: shirt, pants, dress, jacket, skirt, shorts, or other.",
                },
            )
            return str(result.get("answer", "other")).lower().strip()
        except Exception:
            return "other"