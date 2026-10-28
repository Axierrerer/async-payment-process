from types import TracebackType
from typing import Protocol, Self

from domain.interfaces.repositories import IOutboxRepository, IPaymentRepository


class IUnitOfWork(Protocol):
    @property
    def payments(self) -> IPaymentRepository: ...

    @property
    def outbox(self) -> IOutboxRepository: ...

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        trace_back: TracebackType | None,
    ) -> None: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...
