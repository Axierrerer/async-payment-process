from typing import Protocol

from domain.payments.entities import Payment


class IWebhookSender(Protocol):
    async def send(self, payment: Payment) -> None: ...
