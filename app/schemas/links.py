import uuid
from datetime import datetime
from app.schemas.base import BaseSchema

class LinkSchema(BaseSchema):
    id: uuid.UUID
    url: str
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