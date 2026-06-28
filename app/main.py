from fastapi import FastAPI

from app.config import config
from app.routers import (
    links,
)

app = FastAPI(
    title=config.app_name,
    description=config.app_description,
    version=config.app_version,
    swagger_ui_parameters={"defaultModelsExpandDepth": -1},
)

app.include_router(links.router)
