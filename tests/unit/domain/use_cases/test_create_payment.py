from collections.abc import Callable
from decimal import Decimal

import pytest

from domain.commands.payment import CreatePaymentCommand
from domain.payments.entities import Payment
from domain.payments.errors import IdempotencyKeyConflictError
from domain.payments.events import PAYMENTS_NEW_EVENT
from domain.use_cases.payment import CreatePaymentUseCase
from tests.unit.domain.use_cases.fakes import FakeUnitOfWork


async def test_new_payment_is_saved_with_outbox_event(
    uow: FakeUnitOfWork, make_payment: Callable[..., Payment]
) -> None:
    payment = make_payment()

    result = await CreatePaymentUseCase(uow).execute(CreatePaymentCommand(entity=payment))

    assert result is payment
    assert list(uow.payments.payments) == [payment.id]
    assert [(m.event_type, m.payload) for m in uow.outbox.messages] == [
        (PAYMENTS_NEW_EVENT, {"payment_id": str(payment.id)})
    ]


async def test_repeated_request_returns_existing_payment(
    uow: FakeUnitOfWork, make_payment: Callable[..., Payment]
) -> None:
    use_case = CreatePaymentUseCase(uow)
    first = await use_case.execute(CreatePaymentCommand(entity=make_payment()))

    second = await use_case.execute(CreatePaymentCommand(entity=make_payment()))

    assert second.id == first.id
    assert len(uow.outbox.messages) == 1


async def test_same_key_with_different_body_raises_conflict(
    uow: FakeUnitOfWork, make_payment: Callable[..., Payment]
) -> None:
    use_case = CreatePaymentUseCase(uow)
    await use_case.execute(CreatePaymentCommand(entity=make_payment(amount=Decimal("100.00"))))

    with pytest.raises(IdempotencyKeyConflictError):
        await use_case.execute(CreatePaymentCommand(entity=make_payment(amount=Decimal("5000.00"))))

    assert len(uow.payments.payments) == 1
    assert len(uow.outbox.messages) == 1
