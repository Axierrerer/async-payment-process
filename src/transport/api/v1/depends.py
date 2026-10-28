import secrets

from fastapi import Header, Security
from fastapi.security import APIKeyHeader
from punq import Container

from core.container import get_container
from core.settings import AllSettings
from transport.api.v1.errors import InvalidApiKeyError

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str | None = Security(api_key_header)) -> None:
    settings: AllSettings = get_container().resolve(AllSettings)
    expected = settings.app.API_KEY.get_secret_value()
    if api_key is None or not secrets.compare_digest(api_key.encode(), expected.encode()):
        raise InvalidApiKeyError()


async def di_container() -> Container:
    return get_container()


async def get_idempotency_key(
    idempotency_key: str = Header(alias="Idempotency-Key"),
) -> str:
    return idempotency_key
