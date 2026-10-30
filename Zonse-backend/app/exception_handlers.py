import logging
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


def _error_response(
    status_code: int,
    code: str,
    message: str,
    *,
    details: list[dict[str, object]] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    error: dict[str, object] = {"code": code, "message": message}
    if details is not None:
        error["details"] = details
    return JSONResponse(
        status_code=status_code,
        content={"error": error},
        headers=headers,
    )


def _http_error(status_code: int) -> tuple[str, str]:
    known_errors = {
        401: ("unauthorized", "Authentication is required"),
        403: ("forbidden", "You do not have permission to perform this action"),
        404: ("not_found", "Resource not found"),
        405: ("method_not_allowed", "Method not allowed"),
        409: ("conflict", "Resource conflict"),
        503: ("service_unavailable", "Service unavailable"),
    }
    if status_code in known_errors:
        return known_errors[status_code]
    try:
        return "http_error", HTTPStatus(status_code).phrase
    except ValueError:
        return "http_error", "Request failed"


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    del request
    code, message = _http_error(exc.status_code)
    return _error_response(
        exc.status_code,
        code,
        message,
        headers=exc.headers,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    del request
    details = [
        {
            "location": list(error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors()
    ]
    return _error_response(
        422,
        "validation_error",
        "Request validation failed",
        details=details,
    )


async def integrity_exception_handler(
    request: Request,
    exc: IntegrityError,
) -> JSONResponse:
    del request
    logger.warning("Database integrity constraint rejected a request")
    return _error_response(409, "conflict", "Resource conflict")


async def database_exception_handler(
    request: Request,
    exc: SQLAlchemyError,
) -> JSONResponse:
    del request
    logger.error("Database operation failed (%s)", type(exc).__name__)
    return _error_response(503, "service_unavailable", "Service unavailable")


async def unexpected_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    del request
    logger.error("Unhandled application error (%s)", type(exc).__name__)
    return _error_response(500, "internal_error", "An unexpected error occurred")


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(IntegrityError, integrity_exception_handler)
    app.add_exception_handler(SQLAlchemyError, database_exception_handler)
    app.add_exception_handler(Exception, unexpected_exception_handler)
