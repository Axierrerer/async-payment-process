import hashlib
import json
from decimal import Decimal
from typing import Any

from domain.payments.enums import Currency


def compute_request_hash(
    *,
    amount: Decimal,
    currency: Currency,
    description: str,
    metadata: dict[str, Any],
    webhook_url: str,
) -> str:
    body = {
        "amount": str(amount.quantize(Decimal("0.01"))),
        "currency": currency.value,
        "description": description,
        "metadata": metadata,
        "webhook_url": webhook_url,
    }
    raw = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode()).hexdigest()
