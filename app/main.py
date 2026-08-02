import os
from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles

from starlette.exceptions import HTTPException
from fastapi.exceptions import RequestValidationError
from app.exceptions import request_validation_exception_handler, http_exception_handler, unhandled_exception_handler

from app.config import config
from app.routers import (
    static,
    links,
)
from app.dependencies.parameters import RequestParameters

from app.middleware.cache import RedisCacheMiddleware
from app.middleware.logging import log_request_middleware
#from app.middleware.errors import ExceptionHandlerMiddleware

#from app.exceptions import register_exception_handlers

def create_app() -> FastAPI:

    app = FastAPI(
        title=config.app_name,
        description=config.app_description,
        version=config.app_version,
        swagger_ui_parameters={"defaultModelsExpandDepth": -1},
        dependencies=[Depends(RequestParameters)]
    )

    app.mount("/static", StaticFiles(directory=config.base_folder + "/../static",html=True), name="static")

    app.add_middleware(RedisCacheMiddleware)
    app.middleware("http")(log_request_middleware)
    #app.add_middleware(ExceptionHandlerMiddleware)
    #app.add_middleware(log_request_middleware)
    #app.add_middleware(RequestLoggingMiddleware)

    app.include_router(static.router)
    app.include_router(links.router)

    app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    # Register exception handlers
    #register_exception_handlers(app)

    return app

app = create_app()
