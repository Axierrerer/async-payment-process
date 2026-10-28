from pathlib import Path

from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)

ENV_PATH = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_PATH / ".env",
        extra="ignore",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


class PostgresSettings(Settings):
    HOST: str = Field(alias="POSTGRES_HOST")
    USER: str = Field(alias="POSTGRES_USER")
    PASSWORD: str = Field(alias="POSTGRES_PASSWORD")
    DB: str = Field(alias="POSTGRES_DB")
    PORT: int = Field(alias="POSTGRES_PORT", default=5432)
    POOL_SIZE: int = Field(alias="POSTGRES_POOL_SIZE")
    MAX_OVERFLOW: int = Field(alias="POSTGRES_MAX_OVERFLOW")
    POOL_PRE_PING: bool = Field(alias="POSTGRES_POOL_PRE_PING")

    @property
    def async_url(self) -> str:
        return f"postgresql+asyncpg://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.DB}"


class RabbitMQSettings(Settings):
    HOST: str = Field(alias="RABBITMQ_HOST")
    PORT: int = Field(alias="RABBITMQ_PORT", default=5672)
    USER: str = Field(alias="RABBITMQ_DEFAULT_USER")
    PASSWORD: str = Field(alias="RABBITMQ_DEFAULT_PASS")

    @property
    def url(self) -> str:
        return f"amqp://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/"


class OutboxSettings(Settings):
    BATCH_SIZE: int = Field(alias="OUTBOX_BATCH_SIZE")
    POLL_INTERVAL: float = Field(alias="OUTBOX_POLL_INTERVAL")


class WebhookSettings(Settings):
    SECRET: SecretStr = Field(alias="WEBHOOK_SECRET")
    TIMEOUT: float = Field(alias="WEBHOOK_TIMEOUT", default=5.0)


class AppSettings(Settings):
    HOST: str = Field(alias="APP_HOST")
    PORT: int = Field(alias="APP_PORT")
    API_KEY: SecretStr = Field(alias="API_KEY")


class AllSettings(BaseModel):
    postgres: PostgresSettings = Field(default_factory=PostgresSettings)
    app: AppSettings = Field(default_factory=AppSettings)
    rabbitmq: RabbitMQSettings = Field(default_factory=RabbitMQSettings)
    outbox: OutboxSettings = Field(default_factory=OutboxSettings)
    webhook: WebhookSettings = Field(default_factory=WebhookSettings)
