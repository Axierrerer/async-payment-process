from dataclasses import dataclass

from core.base_errors import BaseAppError


@dataclass
class InvalidPaymentAmountError(BaseAppError):
    code: str = "invalid-payment-amount"
    message: str | None = "Payment amount must be greater than zero"


@dataclass
class PaymentAlreadyProcessedError(BaseAppError):
    code: str = "payment-already-processed"
    message: str | None = "Payment has already been processed"


@dataclass
class IdempotencyKeyConflictError(BaseAppError):
    code: str = "idempotency-key-conflict"
    message: str | None = "Idempotency key has already been used with a different request"


@dataclass
class PaymentNotFoundError(BaseAppError):
    code: str = "payment-not-found"
    message: str | None = "Payment not found"


@dataclass
class WebhookDeliveryError(BaseAppError):
    code: str = "webhook-delivery-failed"
    message: str | None = "Failed to deliver webhook"
