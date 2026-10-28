from collections.abc import Callable
from decimal import Decimal

import pytest

from domain.payments.entities import Payment
from domain.payments.enums import Currency


@pytest.fixture
def payment() -> Payment:
    return Payment(
        amount=Decimal("100.00"),
        currency=Currency.RUB,
        description="test",
        idempotency_key="key-1",
        webhook_url="https://example.com/webhook",
    )


@pytest.fixture
def payment_with_amount() -> Callable[[Decimal], Payment]:
    def factory(amount: Decimal) -> Payment:
        return Payment(
            amount=amount,
            currency=Currency.RUB,
            description="test",
            idempotency_key="key-1",
            webhook_url="https://example.com/webhook",
        )

    return factory
