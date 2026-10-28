from collections.abc import Iterator
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from faststream.rabbit import RabbitBroker

from domain.payments.errors import WebhookDeliveryError
from domain.use_cases.payment import ProcessPaymentUseCase
from infra.rabbitmq.topology import PAYMENTS_NEW_RETRY_QUEUES, PAYMENTS_RETRY_EXCHANGE
from transport.rabbitmq.payments.handlers import RETRY_ATTEMPT_HEADER, process_payment
from transport.rabbitmq.payments.schemas import PaymentCreatedMsg


@pytest.fixture
def broker() -> AsyncMock:
    return AsyncMock(spec=RabbitBroker)


@pytest.fixture
def use_case() -> AsyncMock:
    use_case = AsyncMock(spec=ProcessPaymentUseCase)
    use_case.execute.side_effect = WebhookDeliveryError()
    return use_case


@pytest.fixture(autouse=True)
def container(broker: AsyncMock, use_case: AsyncMock) -> Iterator[MagicMock]:
    container = MagicMock()
    container.resolve.side_effect = {ProcessPaymentUseCase: use_case, RabbitBroker: broker}.get
    with patch("transport.rabbitmq.payments.handlers.get_container", return_value=container):
        yield container


def make_message(attempt: int) -> MagicMock:
    message = MagicMock(headers={RETRY_ATTEMPT_HEADER: attempt}, message_id="message-1")
    message.ack = AsyncMock()
    return message


async def test_failed_message_is_sent_to_next_retry_queue(broker: AsyncMock) -> None:
    message = make_message(attempt=0)

    await process_payment(PaymentCreatedMsg(payment_id=uuid4()), message)

    publish = broker.publish.await_args
    assert publish is not None
    assert publish.kwargs["exchange"] == PAYMENTS_RETRY_EXCHANGE
    assert publish.kwargs["routing_key"] == PAYMENTS_NEW_RETRY_QUEUES[0].routing_key
    assert publish.kwargs["headers"] == {RETRY_ATTEMPT_HEADER: 1}
    message.ack.assert_awaited_once()


async def test_message_goes_to_dlq_after_last_retry(broker: AsyncMock) -> None:
    message = make_message(attempt=len(PAYMENTS_NEW_RETRY_QUEUES))

    with pytest.raises(WebhookDeliveryError):
        await process_payment(PaymentCreatedMsg(payment_id=uuid4()), message)

    broker.publish.assert_not_awaited()
    message.ack.assert_not_awaited()
