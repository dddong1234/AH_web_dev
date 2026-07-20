from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.auth.exceptions import AppBaseException, ValidationErrorException


async def app_exception_handler(_: Request, exc: AppBaseException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "message": exc.message,
        },
    )


async def validation_exception_handler(_: Request, __: RequestValidationError) -> JSONResponse:
    validation_error = ValidationErrorException()
    return JSONResponse(
        status_code=validation_error.status_code,
        content={
            "code": validation_error.code,
            "message": validation_error.message,
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppBaseException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
