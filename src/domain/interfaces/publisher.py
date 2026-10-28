from typing import Protocol

from domain.outbox.entities import OutboxMessage


class IEventPublisher(Protocol):
    async def publish(self, message: OutboxMessage) -> None: ...
