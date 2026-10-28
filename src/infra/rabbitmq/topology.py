from faststream.rabbit import ExchangeType, RabbitBroker, RabbitExchange, RabbitQueue

from domain.payments.events import PAYMENTS_NEW_EVENT

PAYMENTS_EXCHANGE = RabbitExchange("payments", type=ExchangeType.DIRECT, durable=True)
PAYMENTS_RETRY_EXCHANGE = RabbitExchange("payments.retry", type=ExchangeType.DIRECT, durable=True)
PAYMENTS_DLX_EXCHANGE = RabbitExchange("payments.dlx", type=ExchangeType.DIRECT, durable=True)

PAYMENTS_NEW_QUEUE = RabbitQueue(
    PAYMENTS_NEW_EVENT,
    durable=True,
    routing_key=PAYMENTS_NEW_EVENT,
    arguments={
        "x-dead-letter-exchange": PAYMENTS_DLX_EXCHANGE.name,
        "x-dead-letter-routing-key": PAYMENTS_NEW_EVENT,
    },
)

RETRY_DELAYS_MS = (2_000, 4_000, 8_000)

PAYMENTS_NEW_RETRY_QUEUES = tuple(
    RabbitQueue(
        f"{PAYMENTS_NEW_EVENT}.retry.{attempt}",
        durable=True,
        routing_key=f"{PAYMENTS_NEW_EVENT}.retry.{attempt}",
        arguments={
            "x-message-ttl": delay_ms,
            "x-dead-letter-exchange": PAYMENTS_EXCHANGE.name,
            "x-dead-letter-routing-key": PAYMENTS_NEW_EVENT,
        },
    )
    for attempt, delay_ms in enumerate(RETRY_DELAYS_MS, start=1)
)

PAYMENTS_NEW_DLQ = RabbitQueue(
    f"{PAYMENTS_NEW_EVENT}.dlq",
    durable=True,
    routing_key=PAYMENTS_NEW_EVENT,
)


async def declare_topology(broker: RabbitBroker) -> None:
    bindings = (
        (PAYMENTS_EXCHANGE, (PAYMENTS_NEW_QUEUE,)),
        (PAYMENTS_RETRY_EXCHANGE, PAYMENTS_NEW_RETRY_QUEUES),
        (PAYMENTS_DLX_EXCHANGE, (PAYMENTS_NEW_DLQ,)),
    )
    for exchange, queues in bindings:
        declared_exchange = await broker.declare_exchange(exchange)
        for queue in queues:
            declared_queue = await broker.declare_queue(queue)
            await declared_queue.bind(declared_exchange, routing_key=queue.routing_key)
