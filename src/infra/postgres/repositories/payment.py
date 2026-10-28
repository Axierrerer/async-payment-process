from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from domain.payments.entities import Payment
from infra.postgres.models import PaymentModel


@dataclass
class PaymentRepository:
    _session: AsyncSession

    async def add_if_not_exists(self, payment: Payment) -> bool:
        stmt = (
            insert(PaymentModel)
            .values(**_to_row(payment))
            .on_conflict_do_nothing(index_elements=[PaymentModel.idempotency_key])
            .returning(PaymentModel.id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_by_id(self, payment_id: UUID) -> Payment | None:
        stmt = select(PaymentModel).where(PaymentModel.id == payment_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def get_by_idempotency_key(self, idempotency_key: str) -> Payment:
        stmt = select(PaymentModel).where(PaymentModel.idempotency_key == idempotency_key)
        result = await self._session.execute(stmt)
        return _to_entity(result.scalar_one())

    async def get_for_update(self, payment_id: UUID) -> Payment | None:
        stmt = select(PaymentModel).where(PaymentModel.id == payment_id).with_for_update()
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return _to_entity(model) if model is not None else None

    async def update(self, payment: Payment) -> None:
        stmt = (
            update(PaymentModel)
            .where(PaymentModel.id == payment.id)
            .values(status=payment.status, processed_at=payment.processed_at)
        )
        await self._session.execute(stmt)


def _to_row(payment: Payment) -> dict[str, Any]:
    return {
        "id": payment.id,
        "amount": payment.amount,
        "currency": payment.currency,
        "description": payment.description,
        "metadata_": payment.metadata,
        "status": payment.status,
        "idempotency_key": payment.idempotency_key,
        "request_hash": payment.request_hash,
        "webhook_url": payment.webhook_url,
        "created_at": payment.created_at,
        "processed_at": payment.processed_at,
    }


def _to_entity(model: PaymentModel) -> Payment:
    return Payment(
        id=model.id,
        amount=model.amount,
        currency=model.currency,
        description=model.description,
        metadata=model.metadata_,
        status=model.status,
        idempotency_key=model.idempotency_key,
        webhook_url=model.webhook_url,
        created_at=model.created_at,
        processed_at=model.processed_at,
    )
