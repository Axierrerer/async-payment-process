import asyncio
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from tests.integration.constants import API_KEY

pytestmark = pytest.mark.integration

PAYMENT_BODY: dict[str, Any] = {
    "amount": "100.00",
    "currency": "RUB",
    "description": "test",
    "metadata": {"order_id": 1},
    "webhook_url": "https://example.com/webhook",
}


def headers(idempotency_key: str) -> dict[str, str]:
    return {"X-API-Key": API_KEY, "Idempotency-Key": idempotency_key}


async def count_rows(engine: AsyncEngine) -> tuple[int, int]:
    async with engine.connect() as connection:
        result = await connection.execute(
            text("SELECT (SELECT count(*) FROM payments), (SELECT count(*) FROM outbox)")
        )
        payments, outbox = result.one()
    return payments, outbox


async def test_create_payment_saves_payment_and_outbox_event(
    client: AsyncClient, engine: AsyncEngine
) -> None:
    response = await client.post("/payments", json=PAYMENT_BODY, headers=headers("key-1"))

    assert response.status_code == 202
    payment_id = response.json()["data"]["payment_id"]
    assert await count_rows(engine) == (1, 1)

    response = await client.get(f"/payments/{payment_id}", headers={"X-API-Key": API_KEY})
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "pending"
    assert response.json()["data"]["amount"] == "100.00"


async def test_repeated_request_returns_same_payment(
    client: AsyncClient, engine: AsyncEngine
) -> None:
    first = await client.post("/payments", json=PAYMENT_BODY, headers=headers("key-1"))
    second = await client.post("/payments", json=PAYMENT_BODY, headers=headers("key-1"))

    assert second.status_code == 202
    assert second.json()["data"]["payment_id"] == first.json()["data"]["payment_id"]
    assert await count_rows(engine) == (1, 1)


async def test_same_key_with_different_body_returns_conflict(
    client: AsyncClient, engine: AsyncEngine
) -> None:
    await client.post("/payments", json=PAYMENT_BODY, headers=headers("key-1"))

    response = await client.post(
        "/payments", json=PAYMENT_BODY | {"amount": "5000.00"}, headers=headers("key-1")
    )

    assert response.status_code == 409
    assert response.json()["errors"][0]["code"] == "idempotency-key-conflict"
    assert await count_rows(engine) == (1, 1)


async def test_concurrent_requests_create_single_payment(
    client: AsyncClient, engine: AsyncEngine
) -> None:
    responses = await asyncio.gather(
        *(client.post("/payments", json=PAYMENT_BODY, headers=headers("key-1")) for _ in range(5))
    )

    assert {response.status_code for response in responses} == {202}
    assert len({response.json()["data"]["payment_id"] for response in responses}) == 1
    assert await count_rows(engine) == (1, 1)


async def test_request_without_api_key_is_rejected(client: AsyncClient) -> None:
    response = await client.get("/payments/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 401
