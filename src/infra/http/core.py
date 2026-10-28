import httpx

from core.settings import AllSettings


def get_http_client(settings: AllSettings) -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=settings.webhook.TIMEOUT)
