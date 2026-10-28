from dataclasses import dataclass
from types import TracebackType

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)

from infra.postgres.repositories.outbox import OutboxRepository
from infra.postgres.repositories.payment import PaymentRepository


@dataclass
class UnitOfWork:
    _session_factory: async_sessionmaker[AsyncSession]

    def __post_init__(self) -> None:
        self.session: AsyncSession = self._session_factory()
        self.payments = PaymentRepository(self.session)
        self.outbox = OutboxRepository(self.session)

    async def __aenter__(self) -> "UnitOfWork":
        await self.session.begin()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        trace_back: TracebackType | None,
    ) -> None:
        try:
            if not exc_value:
                await self.commit()
            else:
                await self.rollback()
        finally:
            await self.close()

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()

    async def close(self) -> None:
        await self.session.close()
