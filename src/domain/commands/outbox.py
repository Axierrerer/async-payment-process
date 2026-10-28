from dataclasses import dataclass


@dataclass(frozen=True)
class PublishOutboxEventsCommand:
    batch_size: int
