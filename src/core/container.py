from functools import lru_cache

import httpx
from faststream.rabbit import RabbitBroker
from punq import Container, Scope
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from core.settings import AllSettings
from domain.interfaces.gateway import IPaymentGateway
from domain.interfaces.publisher import IEventPublisher
from domain.interfaces.uow import IUnitOfWork
from domain.interfaces.webhook import IWebhookSender
from domain.use_cases.outbox import PublishOutboxEventsUseCase
from domain.use_cases.payment import (
    CreatePaymentUseCase,
    GetPaymentUseCase,
    ProcessPaymentUseCase,
)
from infra.gateway.emulator import EmulatedPaymentGateway
from infra.http.core import get_http_client
from infra.http.webhook import HttpWebhookSender
from infra.postgres.core import get_async_session_factory, get_engine
from infra.rabbitmq.core import get_broker
from infra.rabbitmq.publisher import RabbitEventPublisher
from infra.uow import UnitOfWork


@lru_cache
def get_container() -> Container:
    container = Container()
    container.register(
        AllSettings,
        factory=lambda: AllSettings(),
        scope=Scope.singleton,
    )
    container.register(
        AsyncEngine,
        factory=lambda: get_engine(container.resolve(AllSettings)),
        scope=Scope.singleton,
    )
    container.register(
        async_sessionmaker[AsyncSession],
        factory=lambda: get_async_session_factory(container.resolve(AsyncEngine)),
        scope=Scope.singleton,
    )
    container.register(
        RabbitBroker,
        factory=lambda: get_broker(container.resolve(AllSettings)),
        scope=Scope.singleton,
    )
    container.register(
        httpx.AsyncClient,
        factory=lambda: get_http_client(container.resolve(AllSettings)),
        scope=Scope.singleton,
    )
    container.register(IUnitOfWork, UnitOfWork, scope=Scope.transient)
    container.register(IEventPublisher, RabbitEventPublisher, scope=Scope.singleton)
    container.register(IPaymentGateway, EmulatedPaymentGateway, scope=Scope.singleton)
    container.register(IWebhookSender, HttpWebhookSender, scope=Scope.singleton)
    container.register(CreatePaymentUseCase, scope=Scope.transient)
    container.register(GetPaymentUseCase, scope=Scope.transient)
    container.register(ProcessPaymentUseCase, scope=Scope.transient)
    container.register(PublishOutboxEventsUseCase, scope=Scope.transient)
    return container
