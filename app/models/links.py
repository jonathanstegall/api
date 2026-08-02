import uuid
from datetime import datetime, timezone
from pydantic import AnyHttpUrl
from app.backend.database.adapters import HttpUrlType
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.models.base import SQLModel

class LinkModel(SQLModel):
    __tablename__ = "link"
    #__table_args__ = {"schema": "myapi"}

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    url: Mapped[AnyHttpUrl] = mapped_column(HttpUrlType)
    title: Mapped[str] = mapped_column("title")
    source: Mapped[str] = mapped_column("source")
    source_id: Mapped[str] = mapped_column("source_id")
    type: Mapped[str] = mapped_column("type")
    date: Mapped[datetime] = mapped_column(default=None)
    saved_date: Mapped[datetime] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(default=None)
    creator: Mapped[str] = mapped_column("creator")
    referrer: Mapped[str] = mapped_column("referrer")
    format: Mapped[str] = mapped_column("format")
    text: Mapped[str] = mapped_column("text")
    data: Mapped[str] = mapped_column("data")
