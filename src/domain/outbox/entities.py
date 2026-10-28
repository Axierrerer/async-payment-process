from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True, kw_only=True)
class OutboxMessage:
    id: UUID
    event_type: str
    payload: dict[str, Any]
    created_at: datetime
