from collections.abc import Callable
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from domain.commands.payment import ProcessPaymentCommand
from domain.interfaces.gateway import IPaymentGateway
from domain.interfaces.webhook import IWebhookSender
from domain.payments.entities import Payment
from domain.payments.enums import PaymentStatus
from domain.payments.errors import PaymentNotFoundError
from domain.use_cases.payment import ProcessPaymentUseCase
from tests.unit.domain.use_cases.fakes import FakeUnitOfWork


@pytest.fixture
def gateway() -> AsyncMock:
    return AsyncMock(spec=IPaymentGateway)


@pytest.fixture
def webhook_sender() -> AsyncMock:
    return AsyncMock(spec=IWebhookSender)


async def test_pending_payment_is_charged_and_webhook_sent(
    uow: FakeUnitOfWork,
    make_payment: Callable[..., Payment],
    gateway: AsyncMock,
    webhook_sender: AsyncMock,
) -> None:
    payment = make_payment()
    uow.payments.payments[payment.id] = payment
    gateway.charge.return_value = True

    await ProcessPaymentUseCase(uow, gateway, webhook_sender).execute(
        ProcessPaymentCommand(payment_id=payment.id)
    )

    gateway.charge.assert_awaited_once()
    assert uow.payments.payments[payment.id].status is PaymentStatus.SUCCEEDED
    webhook_sender.send.assert_awaited_once()


async def test_processed_payment_is_not_charged_again(
    uow: FakeUnitOfWork,
    make_payment: Callable[..., Payment],
    gateway: AsyncMock,
    webhook_sender: AsyncMock,
) -> None:
    payment = make_payment()
    payment.mark_failed()
    uow.payments.payments[payment.id] = payment

    await ProcessPaymentUseCase(uow, gateway, webhook_sender).execute(
        ProcessPaymentCommand(payment_id=payment.id)
    )

    gateway.charge.assert_not_awaited()
    assert uow.payments.payments[payment.id].status is PaymentStatus.FAILED
    webhook_sender.send.assert_awaited_once()


async def test_missing_payment_raises_not_found(
    uow: FakeUnitOfWork, gateway: AsyncMock, webhook_sender: AsyncMock
) -> None:
    with pytest.raises(PaymentNotFoundError):
        await ProcessPaymentUseCase(uow, gateway, webhook_sender).execute(
            ProcessPaymentCommand(payment_id=uuid4())
        )

    webhook_sender.send.assert_not_awaited()
