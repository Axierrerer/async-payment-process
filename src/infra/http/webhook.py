import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Any

import httpx

from core.settings import AllSettings
from domain.payments.entities import Payment
from domain.payments.errors import WebhookDeliveryError


@dataclass
class HttpWebhookSender:
    _client: httpx.AsyncClient
    _settings: AllSettings

    async def send(self, payment: Payment) -> None:
        body = json.dumps(_to_payload(payment), separators=(",", ":")).encode()
        timestamp = str(int(time.time()))
        secret = self._settings.webhook.SECRET.get_secret_value().encode()
        signature = hmac.new(secret, f"{timestamp}.".encode() + body, hashlib.sha256).hexdigest()
        headers = {
            "Content-Type": "application/json",
            "X-Idempotency-Key": str(payment.id),
            "X-Webhook-Timestamp": timestamp,
            "X-Webhook-Signature": f"sha256={signature}",
        }
        try:
            response = await self._client.post(payment.webhook_url, content=body, headers=headers)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise WebhookDeliveryError(
                details={"payment_id": str(payment.id), "reason": repr(exc)}
            ) from exc


def _to_payload(payment: Payment) -> dict[str, Any]:
    return {
        "payment_id": str(payment.id),
        "status": payment.status.value,
        "amount": str(payment.amount),
        "currency": payment.currency.value,
        "processed_at": payment.processed_at.isoformat() if payment.processed_at else None,
    }
