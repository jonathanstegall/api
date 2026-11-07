import uuid
from datetime import datetime
from pydantic import AnyHttpUrl
from app.backend.database.adapters import HttpUrlType
from app.schemas.base import BaseSchema


class LinkSchema(BaseSchema):
    id: uuid.UUID
    url: AnyHttpUrl
    title: str
    source: str
    source_id: str
    type: str | None = None
    date: datetime | None = None
    creator: str | None = None
    referrer: str | None = None
    text: str | None = None
    saved_date: datetime | None = None
    created_at: datetime | None = None
    format: str | None = None


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
    created_at: datetime


class UpdateLinkSchema(BaseSchema):
    id: uuid.UUID
    url: HttpUrlType
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
    updated_at: datetime


