import asyncio
import logging

import httpx
from faststream import FastStream
from faststream.rabbit import RabbitBroker
from sqlalchemy.ext.asyncio import AsyncEngine

from core.container import get_container
from infra.rabbitmq.topology import declare_topology
from transport.rabbitmq.payments.handlers import router as payments_router


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    container = get_container()
    broker: RabbitBroker = container.resolve(RabbitBroker)
    broker.include_router(payments_router)

    async def on_startup() -> None:
        await broker.connect()
        await declare_topology(broker)

    async def after_shutdown() -> None:
        http_client: httpx.AsyncClient = container.resolve(httpx.AsyncClient)
        engine: AsyncEngine = container.resolve(AsyncEngine)
        await http_client.aclose()
        await engine.dispose()

    app = FastStream(broker, on_startup=[on_startup], after_shutdown=[after_shutdown])
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
