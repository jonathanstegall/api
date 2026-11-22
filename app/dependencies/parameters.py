from datetime import datetime
from typing import Any

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


class IngestionParameters(RequestParameters):
    # Per-source options dict; maps source name -> dict of source-specific options
    # Example: {"raindrop": {"id": 123, "perpage": 20}, "instapaper": {"limit": 10}}
    source_options: dict[str, Any] | None = None

# For backwards compatibility: Re-export the original RequestParameters name

