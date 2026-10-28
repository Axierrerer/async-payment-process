from datetime import UTC, datetime
from types import TracebackType
from typing import Any, Self
from uuid import UUID, uuid4

from domain.outbox.entities import OutboxMessage
from domain.payments.entities import Payment


class FakePaymentRepository:
    def __init__(self) -> None:
        self.payments: dict[UUID, Payment] = {}

    async def add_if_not_exists(self, payment: Payment) -> bool:
        if any(p.idempotency_key == payment.idempotency_key for p in self.payments.values()):
            return False
        self.payments[payment.id] = payment
        return True

    async def get_by_id(self, payment_id: UUID) -> Payment | None:
        return self.payments.get(payment_id)

    async def get_by_idempotency_key(self, idempotency_key: str) -> Payment:
        return next(p for p in self.payments.values() if p.idempotency_key == idempotency_key)

    async def get_for_update(self, payment_id: UUID) -> Payment | None:
        return self.payments.get(payment_id)

    async def update(self, payment: Payment) -> None:
        self.payments[payment.id] = payment


class FakeOutboxRepository:
    def __init__(self) -> None:
        self.messages: list[OutboxMessage] = []
        self.published: list[UUID] = []

    async def add(self, event_type: str, payload: dict[str, Any]) -> None:
        self.messages.append(
            OutboxMessage(
                id=uuid4(),
                event_type=event_type,
                payload=payload,
                created_at=datetime.now(UTC),
            )
        )

    async def get_unpublished(self, limit: int) -> list[OutboxMessage]:
        return [m for m in self.messages if m.id not in self.published][:limit]

    async def mark_published(self, ids: list[UUID]) -> None:
        self.published.extend(ids)


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.payments = FakePaymentRepository()
        self.outbox = FakeOutboxRepository()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        trace_back: TracebackType | None,
    ) -> None:
        return None

    async def commit(self) -> None:
        return None

    async def rollback(self) -> None:
        return None
