from unittest.mock import AsyncMock

from domain.commands.outbox import PublishOutboxEventsCommand
from domain.interfaces.publisher import IEventPublisher
from domain.payments.events import PAYMENTS_NEW_EVENT
from domain.use_cases.outbox import PublishOutboxEventsUseCase
from tests.unit.domain.use_cases.fakes import FakeUnitOfWork


async def test_failed_publish_keeps_remaining_messages_unpublished(uow: FakeUnitOfWork) -> None:
    for number in range(3):
        await uow.outbox.add(PAYMENTS_NEW_EVENT, {"payment_id": str(number)})
    first = uow.outbox.messages[0]
    publisher = AsyncMock(spec=IEventPublisher)
    publisher.publish.side_effect = [None, ConnectionError("broker is down"), None]

    published = await PublishOutboxEventsUseCase(uow, publisher).execute(
        PublishOutboxEventsCommand(batch_size=10)
    )

    assert published == 1
    assert uow.outbox.published == [first.id]
    assert publisher.publish.await_count == 2
