"""Payment routes — Transbank WebPay Plus REST API integration."""

import json
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
        import urllib.request
        import urllib.error

        payload = json.dumps({
            "buy_order": buy_order,
            "session_id": user.user_id,
            "amount": amount,
            "return_url": return_url,
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{base_url}/rswebpaytransaction/api/v1.2/transactions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Tbk-Api-Key-Id": commerce_code,
                "Tbk-Api-Key-Secret": api_key,
            },
        )

        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())

        now = datetime.utcnow().isoformat()
        period_end = (datetime.utcnow() + timedelta(days=30)).isoformat()

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

    except urllib.error.HTTPError:
        raise HTTPException(status_code=502, detail="Payment gateway error")
    except Exception:
        raise HTTPException(status_code=500, detail="Payment creation failed")


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
        import urllib.request
        import urllib.error

        req = urllib.request.Request(
            f"{base_url}/rswebpaytransaction/api/v1.2/transactions/{body.token}",
            method="PUT",
            headers={
                "Content-Type": "application/json",
                "Tbk-Api-Key-Id": commerce_code,
                "Tbk-Api-Key-Secret": api_key,
            },
        )

        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())

        if data.get("response_code") == 0 and data.get("status") == "AUTHORIZED":
            payment = await db.db.prepare(
                "SELECT * FROM payments WHERE transbank_token = ?"
            ).bind(body.token).first()

            if payment:
                uid = payment.get("user_id")

                await db.db.prepare(
                    "UPDATE users SET is_premium = 1, plan_type = 'premium' WHERE id = ?"
                ).bind(uid).run()

                await db.db.prepare(
                    "UPDATE payments SET status = 'completed' WHERE transbank_token = ?"
                ).bind(body.token).run()

                return {"status": "success", "response_code": data.get("response_code")}
            else:
                return {"status": "error", "detail": "Payment record not found"}
        else:
            await db.db.prepare(
                "UPDATE payments SET status = 'failed' WHERE transbank_token = ?"
            ).bind(body.token).run()
            return {"status": "error", "response_code": data.get("response_code")}

    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else str(e)
        return {"status": "error", "detail": error_body}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@router.post("/webhook")
async def payment_webhook(
    request: Request,
):
    """Handle Transbank webhook notification."""
    env = get_env(request)
    db = get_db(request)

    commerce_code = getattr(env, "TRANSBANK_COMMERCE_CODE", "")
    api_key = getattr(env, "TRANSBANK_API_KEY", "")
    base_url = getattr(env, "TRANSBANK_BASE_URL", "https://webpay3gint.transbank.cl")

    body = await request.json()
    token = body.get("token_ws") or body.get("token")

    if not token:
        return {"status": "error", "detail": "No token provided"}

    # Verify token exists in our DB before calling Transbank (prevents abuse)
    payment = await db.db.prepare(
        "SELECT * FROM payments WHERE transbank_token = ?"
    ).bind(token).first()

    if not payment:
        return {"status": "error", "detail": "Unknown token"}

    if payment.get("status") == "completed":
        return {"status": "ok"}  # Already processed

    try:
        import urllib.request
        import urllib.error

        req = urllib.request.Request(
            f"{base_url}/rswebpaytransaction/api/v1.2/transactions/{token}",
            method="PUT",
            headers={
                "Content-Type": "application/json",
                "Tbk-Api-Key-Id": commerce_code,
                "Tbk-Api-Key-Secret": api_key,
            },
        )

        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())

        if data.get("response_code") == 0 and data.get("status") == "AUTHORIZED":
            uid = payment.get("user_id")
            await db.db.prepare(
                "UPDATE users SET is_premium = 1, plan_type = 'premium' WHERE id = ?"
            ).bind(uid).run()
            await db.db.prepare(
                "UPDATE payments SET status = 'completed' WHERE transbank_token = ?"
            ).bind(token).run()

        return {"status": "ok"}

    except urllib.error.HTTPError:
        return {"status": "error", "detail": "Transbank communication failed"}
    except Exception:
        return {"status": "error", "detail": "Internal error"}


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
