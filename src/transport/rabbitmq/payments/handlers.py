import logging

from faststream import AckPolicy
from faststream.rabbit import Channel, RabbitBroker, RabbitMessage, RabbitRouter

from core.container import get_container
from domain.commands.payment import ProcessPaymentCommand
from domain.payments.errors import PaymentNotFoundError
from domain.use_cases.payment import ProcessPaymentUseCase
from infra.rabbitmq.topology import (
    PAYMENTS_EXCHANGE,
    PAYMENTS_NEW_QUEUE,
    PAYMENTS_NEW_RETRY_QUEUES,
    PAYMENTS_RETRY_EXCHANGE,
)
from transport.rabbitmq.payments.schemas import PaymentCreatedMsg

logger = logging.getLogger(__name__)

RETRY_ATTEMPT_HEADER = "x-retry-attempt"

router = RabbitRouter()


@router.subscriber(
    PAYMENTS_NEW_QUEUE,
    PAYMENTS_EXCHANGE,
    channel=Channel(prefetch_count=1),
    ack_policy=AckPolicy.REJECT_ON_ERROR,
)
async def process_payment(body: PaymentCreatedMsg, message: RabbitMessage) -> None:
    container = get_container()
    use_case: ProcessPaymentUseCase = container.resolve(ProcessPaymentUseCase)
    attempt = int(message.headers.get(RETRY_ATTEMPT_HEADER, 0))
    try:
        await use_case.execute(ProcessPaymentCommand(payment_id=body.payment_id))
    except PaymentNotFoundError:
        logger.error("Payment %s not found, sending message to DLQ", body.payment_id)
        raise
    except Exception:
        if attempt >= len(PAYMENTS_NEW_RETRY_QUEUES):
            logger.exception(
                "Payment %s failed after %d retries, sending message to DLQ",
                body.payment_id,
                attempt,
            )
            raise
        retry_queue = PAYMENTS_NEW_RETRY_QUEUES[attempt]
        logger.warning(
            "Payment %s processing failed (attempt %d), retrying via %s",
            body.payment_id,
            attempt + 1,
            retry_queue.name,
            exc_info=True,
        )
        broker: RabbitBroker = container.resolve(RabbitBroker)
        await broker.publish(
            body,
            exchange=PAYMENTS_RETRY_EXCHANGE,
            routing_key=retry_queue.routing_key,
            headers={RETRY_ATTEMPT_HEADER: attempt + 1},
            message_id=message.message_id,
            persist=True,
            mandatory=True,
        )
        await message.ack()
