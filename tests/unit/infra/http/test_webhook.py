import hashlib
import hmac
from collections.abc import Callable
from types import SimpleNamespace
from typing import cast

import httpx
import pytest
from pydantic import SecretStr

from core.settings import AllSettings
from domain.payments.entities import Payment
from domain.payments.errors import WebhookDeliveryError
from infra.http.webhook import HttpWebhookSender

SECRET = "test-secret"


@pytest.fixture
def settings() -> AllSettings:
    return cast(AllSettings, SimpleNamespace(webhook=SimpleNamespace(SECRET=SecretStr(SECRET))))


async def test_webhook_is_signed(
    settings: AllSettings, make_payment: Callable[..., Payment]
) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200)

    sender = HttpWebhookSender(httpx.AsyncClient(transport=httpx.MockTransport(handler)), settings)
    await sender.send(make_payment())

    (request,) = requests
    timestamp = request.headers["X-Webhook-Timestamp"]
    expected = hmac.new(
        SECRET.encode(), f"{timestamp}.".encode() + request.content, hashlib.sha256
    ).hexdigest()
    assert request.headers["X-Webhook-Signature"] == f"sha256={expected}"


async def test_non_2xx_response_raises_delivery_error(
    settings: AllSettings, make_payment: Callable[..., Payment]
) -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(500))
    sender = HttpWebhookSender(httpx.AsyncClient(transport=transport), settings)

    with pytest.raises(WebhookDeliveryError):
        await sender.send(make_payment())
