"""Payment routes — Transbank WebPay Plus REST API integration."""

import json
import time
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
import js
from pyodide.ffi import to_js as _to_js
from js import Object

from middleware.security import require_auth, safe_error_message

router = APIRouter()


def to_js(obj):
    """Convert Python objects to JS with dict_converter for proper dict->Object mapping."""
    return _to_js(obj, dict_converter=Object.fromEntries)


def get_db(request: Request):
    return request.app.state.db


def get_env(request: Request):
    return getattr(request.app.state, "env", None)


def _transbank_headers(commerce_code, api_key):
    return {
        "Content-Type": "application/json",
        "Tbk-Api-Key-Id": commerce_code,
        "Tbk-Api-Key-Secret": api_key,
    }


class CreatePaymentRequest(BaseModel):
    plan_type: str = "premium"


class ConfirmPaymentRequest(BaseModel):
    token: str


@router.post("/create")
async def create_payment(
    body: CreatePaymentRequest,
    request: Request,
    user: dict = Depends(require_auth),
):
    """Create a Transbank WebPay Plus transaction."""
    env = get_env(request)
    db = get_db(request)

    if body.plan_type != "premium":
        raise HTTPException(status_code=400, detail="Invalid plan type")

    user_obj = await db.get_user_by_id(user.user_id)
    if not user_obj:
        raise HTTPException(status_code=404, detail="User not found")

    commerce_code = getattr(env, "TRANSBANK_COMMERCE_CODE", "")
    api_key = getattr(env, "TRANSBANK_API_KEY", "")
    base_url = getattr(env, "TRANSBANK_BASE_URL", "https://webpay3gint.transbank.cl")

    if not commerce_code or not api_key:
        raise HTTPException(status_code=500, detail="Payment configuration missing")

    buy_order = f"FT{user.user_id[:8]}{int(time.time())}"
    amount = 4990
    return_url = getattr(env, "TRANSBANK_RETURN_URL", "https://thelineone.com/payment/success")

    try:
        payload = json.dumps({
            "buy_order": buy_order,
            "session_id": user.user_id,
            "amount": amount,
            "return_url": return_url,
        })

        resp = await js.fetch(
            f"{base_url}/rswebpaytransaction/api/webpay/v1.2/transactions",
            to_js({
                "method": "POST",
                "headers": _transbank_headers(commerce_code, api_key),
                "body": payload,
            })
        )

        text = await resp.text()
        data = json.loads(text)

        if int(resp.status) >= 400:
            raise HTTPException(status_code=502, detail=f"Transbank error: {data}")

        now = datetime.now(timezone.utc).isoformat()
        period_end = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()

        await db.db.prepare(
            """INSERT INTO payments (id, user_id, amount, currency, status, transbank_token, plan_type, period_start, period_end)
               VALUES (?, ?, ?, 'CLP', 'pending', ?, ?, ?, ?)"""
        ).bind(
            user.user_id + "-" + buy_order,
            user.user_id,
            amount,
            data.get("token", ""),
            body.plan_type,
            now,
            period_end,
        ).run()

        return {
            "token": data.get("token"),
            "url": data.get("url"),
            "buy_order": buy_order,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Payment creation failed: {safe_error_message(e, request)}")


@router.post("/confirm")
async def confirm_payment(
    body: ConfirmPaymentRequest,
    request: Request,
    user: dict = Depends(require_auth),
):
    """Confirm a Transbank transaction after user returns from payment page."""
    env = get_env(request)
    db = get_db(request)

    commerce_code = getattr(env, "TRANSBANK_COMMERCE_CODE", "")
    api_key = getattr(env, "TRANSBANK_API_KEY", "")
    base_url = getattr(env, "TRANSBANK_BASE_URL", "https://webpay3gint.transbank.cl")

    if not commerce_code or not api_key:
        raise HTTPException(status_code=500, detail="Payment configuration missing")

    try:
        resp = await js.fetch(
            f"{base_url}/rswebpaytransaction/api/webpay/v1.2/transactions/{body.token}",
            to_js({
                "method": "PUT",
                "headers": _transbank_headers(commerce_code, api_key),
            })
        )

        text = await resp.text()
        data = json.loads(text)

        if int(resp.status) >= 400:
            return {"status": "error", "detail": f"Transbank error: {data}"}

        if data.get("response_code") == 0 and data.get("status") == "AUTHORIZED":
            payment = await db.db.prepare(
                "SELECT * FROM payments WHERE transbank_token = ?"
            ).bind(body.token).first()

            if not payment:
                return {"status": "error", "detail": "Payment record not found"}

            if payment.get("user_id") != user.user_id:
                return {"status": "error", "detail": "Unauthorized: token belongs to another user"}

            uid = payment.get("user_id")

            await db.db.prepare(
                "UPDATE users SET is_premium = 1, plan_type = 'premium' WHERE id = ?"
            ).bind(uid).run()

            await db.db.prepare(
                "UPDATE payments SET status = 'completed' WHERE transbank_token = ?"
            ).bind(body.token).run()

            return {"status": "success", "response_code": data.get("response_code")}
        else:
            await db.db.prepare(
                "UPDATE payments SET status = 'failed' WHERE transbank_token = ?"
            ).bind(body.token).run()
            return {"status": "error", "response_code": data.get("response_code")}

    except Exception as e:
        return {"status": "error", "detail": str(e)}


@router.post("/webhook")
async def payment_webhook(
    request: Request,
):
    """Handle Transbank webhook notification.

    Security: Transbank REST API does not send HMAC signatures on webhooks.
    Verification relies on:
    1. Token must exist in our DB (prevents arbitrary token injection)
    2. Payment must be in 'pending' status (prevents replay attacks)
    3. We call Transbank's API to verify the transaction status (requires API key)
    4. Only AUTHORIZED transactions upgrade the user
    """
    env = get_env(request)
    db = get_db(request)

    commerce_code = getattr(env, "TRANSBANK_COMMERCE_CODE", "")
    api_key = getattr(env, "TRANSBANK_API_KEY", "")
    base_url = getattr(env, "TRANSBANK_BASE_URL", "https://webpay3gint.transbank.cl")

    body = await request.json()
    token = body.get("token_ws") or body.get("token")

    if not token:
        return {"status": "error", "detail": "No token provided"}

    payment = await db.db.prepare(
        "SELECT * FROM payments WHERE transbank_token = ?"
    ).bind(token).first()

    if not payment:
        return {"status": "error", "detail": "Unknown token"}

    if payment.get("status") == "completed":
        return {"status": "ok"}

    if payment.get("status") != "pending":
        return {"status": "error", "detail": "Payment is no longer pending"}

    try:
        resp = await js.fetch(
            f"{base_url}/rswebpaytransaction/api/webpay/v1.2/transactions/{token}",
            to_js({
                "method": "PUT",
                "headers": _transbank_headers(commerce_code, api_key),
            })
        )

        text = await resp.text()
        data = json.loads(text)

        if int(resp.status) >= 400:
            return {"status": "error", "detail": f"Transbank error: {data}"}

        if data.get("response_code") == 0 and data.get("status") == "AUTHORIZED":
            uid = payment.get("user_id")
            await db.db.prepare(
                "UPDATE users SET is_premium = 1, plan_type = 'premium' WHERE id = ?"
            ).bind(uid).run()
            await db.db.prepare(
                "UPDATE payments SET status = 'completed' WHERE transbank_token = ?"
            ).bind(token).run()
        else:
            await db.db.prepare(
                "UPDATE payments SET status = 'failed' WHERE transbank_token = ?"
            ).bind(token).run()

        return {"status": "ok"}

    except Exception as e:
        return {"status": "error", "detail": str(e)}


@router.get("/status")
async def payment_status(
    request: Request,
    user: dict = Depends(require_auth),
):
    """Check user's payment/subscription status."""
    db = get_db(request)
    user_obj = await db.get_user_by_id(user.user_id)

    if not user_obj:
        raise HTTPException(status_code=404, detail="User not found")

    last_payment = await db.db.prepare(
        "SELECT * FROM payments WHERE user_id = ? ORDER BY created_at DESC LIMIT 1"
    ).bind(user.user_id).first()

    return {
        "is_premium": getattr(user_obj, 'is_premium', False),
        "plan_type": getattr(user_obj, 'plan_type', 'free'),
        "last_payment": {
            "status": last_payment.get("status") if last_payment else None,
            "period_end": last_payment.get("period_end") if last_payment else None,
            "amount": last_payment.get("amount") if last_payment else None,
        } if last_payment else None,
    }
