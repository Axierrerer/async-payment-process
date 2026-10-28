from dataclasses import dataclass, field
from typing import Any


@dataclass
class BaseAppError(Exception):
    code: str = "base-app-error"
    message: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def error_body(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }

    def __str__(self) -> str:
        return self.message or self.code
