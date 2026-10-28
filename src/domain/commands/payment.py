from dataclasses import dataclass
from uuid import UUID

from domain.payments.entities import Payment


@dataclass(frozen=True)
class CreatePaymentCommand:
    entity: Payment


@dataclass(frozen=True)
class GetPaymentCommand:
    payment_id: UUID


@dataclass(frozen=True)
class ProcessPaymentCommand:
    payment_id: UUID
