"""YouCam AI Clothes Virtual Try-On service — V3.0.

Workflow (V3.0 — simplified):
  1. Start  → POST /s2s/v3.0/task/cloth  → get task_id
  2. Poll   → GET  /s2s/v3.0/task/cloth/{task_id} → get results

No File API, no presigned URLs, no byte uploads.
Just pass image URLs directly.

Resilience features:
  - Retry with exponential backoff on transient errors
  - Timeout on fetch calls (15s for create, 10s for poll)
"""

import json
import hmac
import hashlib
import base64
import asyncio
import js
from pyodide.ffi import to_js as _to_js
from js import Object


def to_js(obj):
    """Convert Python objects to JS with dict_converter for proper dict→Object mapping."""
    return _to_js(obj, dict_converter=Object.fromEntries)


YOUCAM_BASE = "https://yce-api-01.makeupar.com"
YOUCAM_TASK_URL = f"{YOUCAM_BASE}/s2s/v3.0/task/cloth"


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
            raise Exception(f"YouCam request timeout after {timeout_ms}ms: {url}")
        raise


class YouCamService:
    """YouCam AI Clothes V3.0 service for virtual try-on."""

    def __init__(self, env):
        self.api_key = env.YOUCAM_API_KEY

    def _auth_headers(self):
        """Build auth headers dict."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def create_task(
        self,
        src_url: str,
        ref_url: str,
        garment_category: str = "auto",
    ) -> str:
        """Start a try-on task. Returns task_id.

        src_url: user photo URL (data URL or public HTTP URL)
        ref_url: garment image URL (public HTTP URL from CDN)
        garment_category: auto | upper_body | lower_body | full_body

        Retries on transient errors (network, 5xx) with exponential backoff.
        Does NOT retry on 4xx (bad request, auth error).
        """
        body = json.dumps({
            "src_file_url": src_url,
            "ref_file_url": ref_url,
            "garment_category": garment_category,
        })

        last_error = None
        for attempt in range(3):
            try:
                resp = await _fetch_with_timeout(
                    YOUCAM_TASK_URL,
                    {
                        "method": "POST",
                        "headers": self._auth_headers(),
                        "body": body,
                    },
                    timeout_ms=15000,
                )

                text = await resp.text()
                data = json.loads(text)

                if int(resp.status) >= 400:
                    error = data.get("error") or data.get("detail") or text
                    error_code = data.get("error_code", "")
                    raise Exception(f"YouCam Task API error ({resp.status}): {error} [{error_code}]")

                task_id = data.get("data", {}).get("task_id")
                if not task_id:
                    raise Exception(f"No task_id returned: {data}")

                return task_id

            except Exception as e:
                last_error = e
                error_str = str(e)

                # Don't retry on auth/bad-request errors (4xx)
                if any(k in error_str for k in ["401", "403", "400", "Invalid", "auth", "permission"]):
                    raise

                # Retry with backoff for transient errors (network, 5xx, timeout)
                if attempt < 2:
                    delay = (2 ** attempt)  # 0s, 1s
                    print(json.dumps({
                        "event": "youcam_create_retry",
                        "attempt": attempt + 1,
                        "delay_ms": delay * 1000,
                        "error": error_str[:200],
                    }))
                    await asyncio.sleep(delay)

        raise last_error

    async def poll_task(self, task_id: str) -> dict:
        """Poll task status.

        Returns:
          { "status": "completed", "output_url": "..." }
          { "status": "processing" }
          { "status": "failed", "error": "..." }

        Retries on transient errors with exponential backoff.
        """
        url = f"{YOUCAM_TASK_URL}/{task_id}"

        last_error = None
        for attempt in range(3):
            try:
                resp = await _fetch_with_timeout(
                    url,
                    {
                        "method": "GET",
                        "headers": self._auth_headers(),
                    },
                    timeout_ms=10000,
                )

                status_code = int(resp.status)
                text = await resp.text()
                data = json.loads(text)

                task_status = data.get("data", {}).get("task_status")

                if status_code == 200 and task_status == "success":
                    results = data.get("data", {}).get("results")
                    if results:
                        if isinstance(results, list):
                            output_url = results[0]
                        elif isinstance(results, dict):
                            output_url = results.get("url") or results.get("image_url") or ""
                        else:
                            output_url = str(results)
                        return {"status": "completed", "output_url": output_url}
                    return {"status": "completed", "output_url": None}

                if task_status == "error":
                    error = data.get("data", {}).get("error", "YouCam task failed")
                    return {"status": "failed", "error": error}

                if status_code == 400:
                    return {"status": "failed", "error": "Invalid task ID"}

                if status_code == 401:
                    return {"status": "failed", "error": "YouCam API key invalid"}

                return {"status": "processing"}

            except Exception as e:
                last_error = e
                error_str = str(e)

                # Don't retry on auth/bad-request errors
                if any(k in error_str for k in ["401", "403", "400", "auth", "permission"]):
                    return {"status": "failed", "error": error_str}

                # Retry with backoff for transient errors
                if attempt < 2:
                    delay = (2 ** attempt)
                    print(json.dumps({
                        "event": "youcam_poll_retry",
                        "attempt": attempt + 1,
                        "delay_ms": delay * 1000,
                        "error": error_str[:200],
                    }))
                    await asyncio.sleep(delay)

        return {"status": "failed", "error": str(last_error) if last_error else "Poll failed"}

    @staticmethod
    def verify_webhook_signature(
        payload: str,
        signature_header: str,
        webhook_secret: str,
    ) -> bool:
        """Verify YouCam webhook signature using HMAC-SHA256.

        YouCam follows Standard Webhooks spec:
          - signature header format: "v1,<base64-hmac>"
          - signing input: "{webhook_id}.{webhook_timestamp}.{body}"
        """
        if not signature_header or not webhook_secret:
            return False

        parts = signature_header.split(",")
        if len(parts) != 2 or parts[0] != "v1":
            return False

        expected_sig = parts[1]

        # Remove whsec_ prefix from secret if present
        secret_bytes = webhook_secret
        if secret_bytes.startswith("whsec_"):
            secret_bytes = secret_bytes[6:]
        secret_bytes = base64.b64decode(secret_bytes)

        computed = hmac.new(secret_bytes, payload.encode("utf-8"), hashlib.sha256)
        computed_b64 = base64.b64encode(computed.digest()).decode("utf-8")

        return hmac.compare_digest(computed_b64, expected_sig)
