import asyncio
import contextlib
import logging
import signal

from faststream.rabbit import RabbitBroker
from sqlalchemy.ext.asyncio import AsyncEngine

from core.container import get_container
from core.settings import AllSettings
from domain.commands.outbox import PublishOutboxEventsCommand
from domain.use_cases.outbox import PublishOutboxEventsUseCase
from infra.rabbitmq.topology import declare_topology

logger = logging.getLogger(__name__)


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    container = get_container()
    settings: AllSettings = container.resolve(AllSettings)
    broker: RabbitBroker = container.resolve(RabbitBroker)
    engine: AsyncEngine = container.resolve(AsyncEngine)

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop.set)

    command = PublishOutboxEventsCommand(batch_size=settings.outbox.BATCH_SIZE)
    await broker.connect()
    try:
        await declare_topology(broker)
        logger.info("Outbox relay started")
        while not stop.is_set():
            use_case: PublishOutboxEventsUseCase = container.resolve(PublishOutboxEventsUseCase)
            try:
                published = await use_case.execute(command)
            except Exception:
                logger.exception("Outbox relay iteration failed")
                published = 0
            if published:
                logger.info("Published %d outbox messages", published)
            if published < command.batch_size:
                with contextlib.suppress(TimeoutError):
                    await asyncio.wait_for(stop.wait(), timeout=settings.outbox.POLL_INTERVAL)
    finally:
        await broker.stop()
        await engine.dispose()
        logger.info("Outbox relay stopped")


if __name__ == "__main__":
    asyncio.run(main())
