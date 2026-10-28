from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from domain.payments.enums import Currency, PaymentStatus
from domain.payments.errors import (
    InvalidPaymentAmountError,
    PaymentAlreadyProcessedError,
)
from domain.payments.request_hash import compute_request_hash


@dataclass(kw_only=True)
class Payment:
    id: UUID = field(default_factory=uuid4)
    amount: Decimal
    currency: Currency
    description: str
    metadata: dict[str, Any] = field(default_factory=dict)
    status: PaymentStatus = PaymentStatus.PENDING
    idempotency_key: str
    request_hash: str = field(init=False)
    webhook_url: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    processed_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.amount <= 0:
            raise InvalidPaymentAmountError(details={"amount": str(self.amount)})
        self.request_hash = compute_request_hash(
            amount=self.amount,
            currency=self.currency,
            description=self.description,
            metadata=self.metadata,
            webhook_url=self.webhook_url,
        )

    @property
    def is_processed(self) -> bool:
        return self.status != PaymentStatus.PENDING

    def mark_succeeded(self) -> None:
        self._finish(PaymentStatus.SUCCEEDED)

    def mark_failed(self) -> None:
        self._finish(PaymentStatus.FAILED)

    def _finish(self, status: PaymentStatus) -> None:
        if self.is_processed:
            raise PaymentAlreadyProcessedError(details={"payment_id": str(self.id)})
        self.status = status
        self.processed_at = datetime.now(UTC)
