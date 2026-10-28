import logging
from dataclasses import dataclass

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from core.base_errors import BaseAppError
from domain.payments.errors import (
    IdempotencyKeyConflictError,
    InvalidPaymentAmountError,
    PaymentNotFoundError,
)
from transport.api.v1.schemas import ApiResponseSchema, ErrorItem

logger = logging.getLogger(__name__)


@dataclass
class InvalidApiKeyError(BaseAppError):
    code: str = "invalid-api-key"
    message: str | None = "Invalid or missing API key"


ERROR_STATUS_CODES: dict[type[BaseAppError], int] = {
    InvalidApiKeyError: status.HTTP_401_UNAUTHORIZED,
    PaymentNotFoundError: status.HTTP_404_NOT_FOUND,
    IdempotencyKeyConflictError: status.HTTP_409_CONFLICT,
    InvalidPaymentAmountError: status.HTTP_422_UNPROCESSABLE_CONTENT,
}


def _error_response(status_code: int, errors: list[ErrorItem]) -> JSONResponse:
    body = ApiResponseSchema[None](errors=errors)
    return JSONResponse(status_code=status_code, content=body.model_dump(mode="json"))


async def app_error_handler(request: Request, exc: BaseAppError) -> JSONResponse:
    status_code = next(
        (ERROR_STATUS_CODES[cls] for cls in type(exc).__mro__ if cls in ERROR_STATUS_CODES),
        status.HTTP_400_BAD_REQUEST,
    )
    error = ErrorItem(code=exc.code, message=exc.message, details=exc.details)
    return _error_response(status_code, [error])


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = [
        ErrorItem(
            code="validation-error",
            message=error["msg"],
            details={"loc": list(error["loc"]), "type": error["type"]},
        )
        for error in exc.errors()
    ]
    return _error_response(status.HTTP_422_UNPROCESSABLE_CONTENT, errors)


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    error = ErrorItem(code="internal-error", message="Internal server error")
    return _error_response(status.HTTP_500_INTERNAL_SERVER_ERROR, [error])
