from uuid import UUID

from pydantic import BaseModel


class PaymentCreatedMsg(BaseModel):
    payment_id: UUID
