from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles

from app.config import config
from app.routers import (
    static,
    links,
)
from app.dependencies.parameters import RequestParameters

from app.middleware.cache import RedisCacheMiddleware

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

    app.include_router(static.router)
    app.include_router(links.router)

    return app

app = create_app()

