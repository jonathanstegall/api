"""Link ORM model - infrastructure layer SQLAlchemy mapping."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

from pydantic import AnyHttpUrl

from app.domain.entities.link import Link
from app.infrastructure.persistence.database import Base

def get_datetime_utc() -> datetime:
    return datetime.now(timezone.utc)

class LinkModel(SQLModel):
    """
    SQLAlchemy ORM model for links table.

    This is an INFRASTRUCTURE detail that maps domain entities to database rows.
    The domain layer never imports this class.
    """

    __tablename__ = "links"
    __table_args__ = (UniqueConstraint("source", "source_id", name="unique_source_item"), )

    source: str | None = Field(default=None, min_length=1, max_length=255)
    source_id: str | None = Field(default=None, min_length=1, max_length=255)
    type: str | None = Field(default=None, min_length=1, max_length=255)
    date: datetime | None = Field(default=None, sa_type=DateTime(timezone=True)) # the date posted by the source, if any
    creator: str | None = Field(default=None, min_length=1, max_length=255)
    referrer: str | None = Field(default=None, min_length=1, max_length=255)
    url: str = Field(min_length=1, max_length=2000)
    data: str | None = Field(default=None)
    title: str = Field(min_length=1, max_length=255)
    text: str | None = Field(default=None)
    saved_date: datetime | None = Field(default=None, sa_type=DateTime(timezone=True)) # the date I saved the link in whatever third party I saved it in
    format: str | None = Field(default=None, min_length=1, max_length=255)

    def __repr__(self) -> str:
        """String representation of LinkModel."""
        return f"LinkModel(id={self.id!r}, url={self.url!r}, title={self.title!r})"

    def to_entity(self) -> Link:
        """
        Convert ORM model to domain entity.

        This mapper method handles the translation between infrastructure
        and domain layers.

        Returns:
            Link domain entity
        """
        return Link(
            id=self.id,
            url=self.url,
            title=self.title,
            source=self.source,
            source_id=self.source_id,
            type=self.type,
            date=self.date,
            creator=self.creator,
            referrer=self.referrer,
            text=self.text,
            saved_date=self.saved_date,
            format=self.format,
            data=self.data,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @staticmethod
    def from_entity(link: Link) -> "LinkModel":
        """
        Create ORM model from domain entity.

        Args:
            link: Domain entity

        Returns:
            ORM model ready for persistence
        """
        model = LinkModel(
            url=link.url,
            title=link.title,
            source=link.source,
            source_id=link.source_id,
            type=link.type,
            date=link.date,
            creator=link.creator,
            referrer=link.referrer,
            text=link.text,
            saved_date=link.saved_date,
            format=link.format,
            data=link.data,
            created_at=link.created_at,
            updated_at=link.updated_at,
        )

        # Set ID if it exists (for updates)
        if link.id is not None:
            model.id = link.id

        # Set timestamps if they exist
        if link.created_at is not None:
            model.created_at = link.created_at
        if link.updated_at is not None:
            model.updated_at = link.updated_at

        return model
