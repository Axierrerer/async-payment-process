from dataclasses import dataclass

from domain.commands.payment import (
    CreatePaymentCommand,
    GetPaymentCommand,
    ProcessPaymentCommand,
)
from domain.interfaces.gateway import IPaymentGateway
from domain.interfaces.uow import IUnitOfWork
from domain.interfaces.webhook import IWebhookSender
from domain.payments.entities import Payment
from domain.payments.errors import IdempotencyKeyConflictError, PaymentNotFoundError
from domain.payments.events import PAYMENTS_NEW_EVENT


@dataclass
class CreatePaymentUseCase:
    _uow: IUnitOfWork

    async def execute(self, command: CreatePaymentCommand) -> Payment:
        payment = command.entity
        async with self._uow as uow:
            if await uow.payments.add_if_not_exists(payment):
                await uow.outbox.add(PAYMENTS_NEW_EVENT, {"payment_id": str(payment.id)})
                return payment

            existing = await uow.payments.get_by_idempotency_key(payment.idempotency_key)
            if existing.request_hash != payment.request_hash:
                raise IdempotencyKeyConflictError(
                    details={"idempotency_key": payment.idempotency_key}
                )
            return existing


@dataclass
class GetPaymentUseCase:
    _uow: IUnitOfWork

    async def execute(self, command: GetPaymentCommand) -> Payment:
        async with self._uow as uow:
            payment = await uow.payments.get_by_id(command.payment_id)
        if payment is None:
            raise PaymentNotFoundError(details={"payment_id": str(command.payment_id)})
        return payment


@dataclass
class ProcessPaymentUseCase:
    _uow: IUnitOfWork
    _gateway: IPaymentGateway
    _webhook_sender: IWebhookSender

    async def execute(self, command: ProcessPaymentCommand) -> None:
        async with self._uow as uow:
            payment = await uow.payments.get_for_update(command.payment_id)
            if payment is None:
                raise PaymentNotFoundError(details={"payment_id": str(command.payment_id)})
            if not payment.is_processed:
                if await self._gateway.charge(payment):
                    payment.mark_succeeded()
                else:
                    payment.mark_failed()
                await uow.payments.update(payment)
        await self._webhook_sender.send(payment)
