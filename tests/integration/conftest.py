import os
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine
from testcontainers.community.postgres import PostgresContainer

from core.container import get_container
from entrypoints.uvicorn_run import create_app
from tests.integration.constants import API_KEY

ALEMBIC_INI = Path(__file__).resolve().parents[2] / "alembic.ini"

TEST_ENV = {
    "POSTGRES_POOL_SIZE": "5",
    "POSTGRES_MAX_OVERFLOW": "5",
    "POSTGRES_POOL_PRE_PING": "true",
    "APP_HOST": "127.0.0.1",
    "APP_PORT": "8000",
    "API_KEY": API_KEY,
    "RABBITMQ_HOST": "localhost",
    "RABBITMQ_DEFAULT_USER": "test",
    "RABBITMQ_DEFAULT_PASS": "test",
    "OUTBOX_BATCH_SIZE": "100",
    "OUTBOX_POLL_INTERVAL": "1.0",
    "WEBHOOK_SECRET": "test-webhook-secret",
}


@pytest.fixture(scope="session", autouse=True)
def postgres() -> Iterator[PostgresContainer]:
    with PostgresContainer("postgres:17-alpine") as pg:
        os.environ.update(
            TEST_ENV
            | {
                "POSTGRES_HOST": pg.get_container_host_ip(),
                "POSTGRES_PORT": str(pg.get_exposed_port(5432)),
                "POSTGRES_USER": pg.username,
                "POSTGRES_PASSWORD": pg.password,
                "POSTGRES_DB": pg.dbname,
            }
        )
        get_container.cache_clear()
        command.upgrade(Config(str(ALEMBIC_INI)), "head")
        yield pg
        get_container.cache_clear()


@pytest.fixture(scope="session")
async def engine(postgres: PostgresContainer) -> AsyncIterator[AsyncEngine]:
    engine: AsyncEngine = get_container().resolve(AsyncEngine)
    yield engine
    await engine.dispose()


@pytest.fixture(autouse=True)
async def clean_tables(engine: AsyncEngine, postgres: PostgresContainer) -> None:
    expected = (postgres.get_container_host_ip(), int(postgres.get_exposed_port(5432)))
    actual = (engine.url.host, engine.url.port)
    assert actual == expected, f"Refusing to truncate non-test database {engine.url!r}"
    async with engine.begin() as connection:
        await connection.execute(text("TRUNCATE payments, outbox"))


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    async with AsyncClient(
        transport=ASGITransport(app=create_app()),
        base_url="http://test/api/v1",
    ) as client:
        yield client
