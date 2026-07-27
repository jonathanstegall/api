from datetime import datetime

from fastapi import FastAPI
from pydantic import BaseModel

from app.config import config

app = FastAPI()


class RequestParameters(BaseModel):
    page: int | None = 1
    page_size: int | None = config.page_size
    order_by: str | None = None
    search: str | None = ""
    saved_date_start: datetime | None = None
    saved_date_end: datetime | None = None

