import uuid
from datetime import datetime
from pydantic import AnyHttpUrl
from app.schemas.base import BaseSchema


class CreateLinkSchema(BaseSchema):
    id: uuid.UUID
    url: AnyHttpUrl
    title: str
    source: str
    source_id: str
    type: str | None
    date: datetime | None
    creator: str | None
    referrer: str | None
    data: str | None
    text: str | None
    saved_date: datetime | None
    format: str | None


class LinkSchema(BaseSchema):
    id: uuid.UUID
    url: AnyHttpUrl
    title: str
    source: str
    source_id: str
    type: str | None
    date: datetime | None
    creator: str | None
    referrer: str | None
    text: str | None
    saved_date: datetime | None
    format: str | None