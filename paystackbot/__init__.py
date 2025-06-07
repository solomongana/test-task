import os
import hmac
import hashlib
from fastapi import Request, HTTPException

PAYSTACK_SECRET = os.getenv("PAYSTACK_SECRET", "")

async def paystack_webhook(request: Request):
    """Handle Paystack webhook verifying signature."""
    signature = request.headers.get("X-Paystack-Signature")
    body = await request.body()
    expected = hmac.new(PAYSTACK_SECRET.encode(), body, hashlib.sha512).hexdigest()
    if not signature or not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=400, detail="Invalid signature")
    return body

