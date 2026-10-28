from collections.abc import Callable
from decimal import Decimal

import pytest

from domain.payments.entities import Payment
from domain.payments.errors import InvalidPaymentAmountError, PaymentAlreadyProcessedError


def test_already_processed_payment(payment: Payment) -> None:
    payment.mark_succeeded()
    with pytest.raises(PaymentAlreadyProcessedError) as exc_info:
        payment.mark_succeeded()

    assert exc_info.value.details["payment_id"] == str(payment.id)


@pytest.mark.parametrize("amount", [Decimal("0"), Decimal("-1"), Decimal("-0.01")])
def test_invalid_payment_amount(
    payment_with_amount: Callable[[Decimal], Payment], amount: Decimal
) -> None:
    with pytest.raises(InvalidPaymentAmountError) as exc_info:
        payment_with_amount(amount)

    assert exc_info.value.details["amount"] == str(amount)
