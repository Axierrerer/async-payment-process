import logging
from dataclasses import dataclass
from uuid import UUID

from domain.commands.outbox import PublishOutboxEventsCommand
from domain.interfaces.publisher import IEventPublisher
from domain.interfaces.uow import IUnitOfWork

logger = logging.getLogger(__name__)


@dataclass
class PublishOutboxEventsUseCase:
    _uow: IUnitOfWork
    _publisher: IEventPublisher

    async def execute(self, command: PublishOutboxEventsCommand) -> int:
        async with self._uow as uow:
            messages = await uow.outbox.get_unpublished(command.batch_size)
            published: list[UUID] = []
            for message in messages:
                try:
                    await self._publisher.publish(message)
                except Exception:
                    logger.exception("Failed to publish outbox message %s", message.id)
                    break
                published.append(message.id)
            await uow.outbox.mark_published(published)
        return len(published)
