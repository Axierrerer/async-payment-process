from dataclasses import dataclass

from faststream.rabbit import RabbitBroker

from domain.outbox.entities import OutboxMessage
from infra.rabbitmq.topology import PAYMENTS_EXCHANGE


@dataclass
class RabbitEventPublisher:
    _broker: RabbitBroker

    async def publish(self, message: OutboxMessage) -> None:
        await self._broker.publish(
            message.payload,
            exchange=PAYMENTS_EXCHANGE,
            routing_key=message.event_type,
            message_id=str(message.id),
            persist=True,
            mandatory=True,
        )
