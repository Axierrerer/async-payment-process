from collections.abc import Callable
from decimal import Decimal
from typing import Any

import pytest

from domain.payments.entities import Payment
from domain.payments.enums import Currency


@pytest.fixture
def make_payment() -> Callable[..., Payment]:
    def factory(**overrides: Any) -> Payment:
        fields: dict[str, Any] = {
            "amount": Decimal("100.00"),
            "currency": Currency.RUB,
            "description": "test",
            "metadata": {"order_id": 1},
            "idempotency_key": "key-1",
            "webhook_url": "https://example.com/webhook",
        }
        return Payment(**(fields | overrides))

    return factory
