from typing import Any

from pydantic import BaseModel, Field


class ErrorItem(BaseModel):
    code: str
    message: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class ApiResponseSchema[T](BaseModel):
    data: T | dict[str, Any] | list[dict[str, Any]] = Field(default_factory=dict)
    meta: dict[str, Any] = Field(default_factory=dict)
    errors: list[ErrorItem] = Field(default_factory=list)
