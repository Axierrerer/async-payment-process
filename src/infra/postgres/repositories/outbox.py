from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from domain.outbox.entities import OutboxMessage
from infra.postgres.models import OutboxModel


@dataclass
class OutboxRepository:
    _session: AsyncSession

    async def add(self, event_type: str, payload: dict[str, Any]) -> None:
        self._session.add(OutboxModel(id=uuid4(), event_type=event_type, payload=payload))

    async def get_unpublished(self, limit: int) -> list[OutboxMessage]:
        stmt = (
            select(OutboxModel)
            .where(OutboxModel.published_at.is_(None))
            .order_by(OutboxModel.created_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        result = await self._session.execute(stmt)
        return [_to_entity(model) for model in result.scalars()]

    async def mark_published(self, ids: list[UUID]) -> None:
        if not ids:
            return
        stmt = update(OutboxModel).where(OutboxModel.id.in_(ids)).values(published_at=func.now())
        await self._session.execute(stmt)


def _to_entity(model: OutboxModel) -> OutboxMessage:
    return OutboxMessage(
        id=model.id,
        event_type=model.event_type,
        payload=model.payload,
        created_at=model.created_at,
    )
