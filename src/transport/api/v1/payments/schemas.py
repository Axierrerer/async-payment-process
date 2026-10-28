from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, UrlConstraints

from domain.payments.entities import Payment
from domain.payments.enums import Currency, PaymentStatus


class CreatePaymentReq(BaseModel):
    amount: Annotated[Decimal, Field(gt=0, max_digits=18, decimal_places=2)]
    currency: Currency
    description: Annotated[str, Field(min_length=1, max_length=255)]
    metadata: dict[str, Any] = Field(default_factory=dict)
    webhook_url: Annotated[HttpUrl, UrlConstraints(max_length=2048)]

    def to_entity(self, idempotency_key: str) -> Payment:
        return Payment(
            amount=self.amount,
            currency=self.currency,
            description=self.description,
            metadata=self.metadata,
            idempotency_key=idempotency_key,
            webhook_url=str(self.webhook_url),
        )


class CreatePaymentResp(BaseModel):
    payment_id: UUID
    status: PaymentStatus
    created_at: datetime

    @classmethod
    def from_entity(cls, payment: Payment) -> "CreatePaymentResp":
        return cls(
            payment_id=payment.id,
            status=payment.status,
            created_at=payment.created_at,
        )


class PaymentResp(BaseModel):
    payment_id: UUID
    amount: Decimal
    currency: Currency
    description: str
    metadata: dict[str, Any]
    status: PaymentStatus
    idempotency_key: str
    webhook_url: str
    created_at: datetime
    processed_at: datetime | None

    @classmethod
    def from_entity(cls, payment: Payment) -> "PaymentResp":
        return cls(
            payment_id=payment.id,
            amount=payment.amount,
            currency=payment.currency,
            description=payment.description,
            metadata=payment.metadata,
            status=payment.status,
            idempotency_key=payment.idempotency_key,
            webhook_url=payment.webhook_url,
            created_at=payment.created_at,
            processed_at=payment.processed_at,
        )
