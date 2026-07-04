"""Virtual Try-On service using Replicate API (cuuupid/idm-vton)."""

import json
import js
from pyodide.ffi import to_js as _to_js
from js import Object


def to_js(obj):
    """Convert Python objects to JS with dict_converter for proper dict→Object mapping."""
    return _to_js(obj, dict_converter=Object.fromEntries)


REPLICATE_VERSION = "0513734a452173b8173e907e3a59d19a36266e55b48528559432bd21c7d7e985"
REPLICATE_API = "https://api.replicate.com/v1/predictions"


class VtonService:
    """VTON service calling Replicate IDM-VTON via REST API."""

    def __init__(self, env):
        self.env = env
        self.token = env.REPLICATE_API_TOKEN

    def _auth_headers(self):
        """Build auth headers dict."""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    async def process_try_on(
        self,
        user_image_url: str,
        garment_image_url: str,
        product_id: str,
        user_id: str,
        category: str = "upper_body",
    ) -> dict:
        """Run virtual try-on: create prediction → poll → return output URL."""
        body_json = json.dumps({
            "version": REPLICATE_VERSION,
            "input": {
                "human_img": user_image_url,
                "garm_img": garment_image_url,
                "category": category,
            }
        })

        # Create prediction
        resp = await js.fetch(REPLICATE_API, to_js({
            "method": "POST",
            "headers": self._auth_headers(),
            "body": body_json,
        }))
        text = await resp.text()
        data = json.loads(text)

        if int(resp.status) >= 400:
            detail = data.get("detail") or data.get("error") or text
            raise Exception(f"Replicate API error ({resp.status}): {detail}")

        prediction_id = data.get("id")
        status = data.get("status")
        if not prediction_id:
            raise Exception(f"No prediction ID returned: {data}")

        # If already done (unlikely), return
        if status == "succeeded":
            output = data.get("output")
            if isinstance(output, list) and len(output) > 0:
                return {"status": "completed", "output_url": output[0]}
            elif isinstance(output, str):
                return {"status": "completed", "output_url": output}
        if status == "failed":
            raise Exception(data.get("error") or "Replicate prediction failed")

        # GET with Prefer: wait — blocks up to 60s until prediction completes
        poll_url = f"{REPLICATE_API}/{prediction_id}"
        poll_entries = to_js([["method", "GET"]])
        poll_opts = js.Object.fromEntries(poll_entries)
        poll_h = js.Headers.new()
        poll_h.append("Authorization", f"Bearer {self.token}")
        poll_h.append("Prefer", "wait")
        poll_opts.headers = poll_h
        poll_resp = await js.fetch(poll_url, poll_opts)
        poll_text = await poll_resp.text()
        data = json.loads(poll_text)
        status = data.get("status")

        if status == "failed":
            raise Exception(data.get("error") or "Replicate prediction failed")
        if status == "canceled":
            raise Exception("Replicate prediction was canceled")
        if status != "succeeded":
            raise Exception(f"Replicate prediction timed out (status={status})")

        output = data.get("output")
        if isinstance(output, list) and len(output) > 0:
            output_url = output[0]
        elif isinstance(output, str):
            output_url = output
        else:
            raise Exception(f"No output URL in Replicate result (status={status})")

        return {"status": "completed", "output_url": output_url}


def _detect_content_type(image_bytes: bytes) -> str:
    if len(image_bytes) < 4:
        return "image/jpeg"
    header = image_bytes[:4]
    if header[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if header == b"\x89PNG":
        return "image/png"
    if header == b"RIFF" and image_bytes[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"


def _validate_image(image_bytes: bytes) -> bool:
    if len(image_bytes) < 4:
        return False
    header = image_bytes[:4]
    if header[:3] == b"\xff\xd8\xff":
        return True
    if header == b"\x89PNG":
        return True
    if header == b"RIFF" and image_bytes[8:12] == b"WEBP":
        return True
    return False
