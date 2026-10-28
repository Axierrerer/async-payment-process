from typing import Protocol

from domain.payments.entities import Payment


class IPaymentGateway(Protocol):
    async def charge(self, payment: Payment) -> bool: ...
