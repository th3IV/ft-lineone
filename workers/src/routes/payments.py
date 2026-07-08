"""Payment routes — Transbank WebPay Plus integration."""

import json
import hashlib
import hmac
import time
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel

from middleware.security import require_auth

router = APIRouter()


def get_db(request: Request):
    return request.app.state.db


def get_env(request: Request):
    return getattr(request.app.state, "env", None)


class CreatePaymentRequest(BaseModel):
    plan_type: str = "premium"


class WebhookRequest(BaseModel):
    token: str


@router.post("/create")
async def create_payment(
    body: CreatePaymentRequest,
    request: Request,
    user: dict = Depends(require_auth),
):
    """Create a Transbank WebPay transaction."""
    env = get_env(request)
    db = get_db(request)

    if body.plan_type != "premium":
        raise HTTPException(status_code=400, detail="Invalid plan type")

    # Get user info
    user_obj = await db.get_user_by_id(user.user_id)
    if not user_obj:
        raise HTTPException(status_code=404, detail="User not found")

    # Transbank credentials
    commerce_code = getattr(env, "TRANSBANK_COMMERCE_CODE", "")
    api_key = getattr(env, "TRANSBANK_API_KEY", "")
    base_url = getattr(env, "TRANSBANK_BASE_URL", "https://webpay3gint.transbank.cl")

    if not commerce_code or not api_key:
        raise HTTPException(status_code=500, detail="Payment configuration missing")

    # Create unique buy order
    buy_order = f"FT{user.user_id[:8]}{int(time.time())}"
    amount = 4990
    return_url = getattr(env, "TRANSBANK_RETURN_URL", "https://thelineone.com/payment/success")

    # Create transaction via Transbank API
    try:
        import urllib.request
        import urllib.error

        payload = json.dumps({
            "buy_order": buy_order,
            "session_id": user.user_id,
            "amount": amount,
            "return_url": return_url,
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{base_url}/rswebpaytransaction/api/v1.0/transactions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"WSK {commerce_code} {api_key}",
            },
        )

        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())

        # Save payment record
        from datetime import datetime as _dt
        now = _dt.utcnow().isoformat()
        period_end = (_dt.utcnow() + timedelta(days=30)).isoformat()

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

    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else str(e)
        raise HTTPException(status_code=502, detail=f"Transbank error: {error_body}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Payment creation failed: {str(e)}")


@router.post("/webhook")
async def payment_webhook(
    body: WebhookRequest,
    request: Request,
):
    """Handle Transbank payment callback."""
    env = get_env(request)
    db = get_db(request)

    commerce_code = getattr(env, "TRANSBANK_COMMERCE_CODE", "")
    api_key = getattr(env, "TRANSBANK_API_KEY", "")
    base_url = getattr(env, "TRANSBANK_BASE_URL", "https://webpay3gint.transbank.cl")

    # Confirm transaction
    try:
        import urllib.request
        import urllib.error

        req = urllib.request.Request(
            f"{base_url}/rswebpaytransaction/api/v1.0/transactions/{body.token}",
            method="PUT",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"WSK {commerce_code} {api_key}",
            },
        )

        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())

        if data.get("response_code") == 0 and data.get("status") == "AUTHORIZED":
            # Payment successful — activate premium
            buy_order = data.get("buy_order", "")
            user_id = buy_order[:8]  # Extract user_id prefix

            # Find payment record and activate
            payment = await db.db.prepare(
                "SELECT * FROM payments WHERE transbank_token = ?"
            ).bind(body.token).first()

            if payment:
                uid = payment.get("user_id", user_id)

                # Update user to premium
                await db.db.prepare(
                    "UPDATE users SET is_premium = 1, plan_type = 'premium' WHERE id = ?"
                ).bind(uid).run()

                # Update payment status
                await db.db.prepare(
                    "UPDATE payments SET status = 'completed' WHERE transbank_token = ?"
                ).bind(body.token).run()

        return {"status": "ok"}

    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else str(e)
        return {"status": "error", "detail": error_body}
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

    # Get last payment
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
