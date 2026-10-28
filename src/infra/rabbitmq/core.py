from faststream.rabbit import Channel, RabbitBroker

from core.settings import AllSettings


def get_broker(settings: AllSettings) -> RabbitBroker:
    return RabbitBroker(
        settings.rabbitmq.url,
        default_channel=Channel(publisher_confirms=True, on_return_raises=True),
    )
