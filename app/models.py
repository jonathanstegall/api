import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

def get_datetime_utc() -> datetime:
    return datetime.now(timezone.utc)

# Shared properties
class LinkBase(SQLModel):

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


# Properties to receive on link creation
class LinkCreate(LinkBase):
    pass


# Properties to receive on link update
class LinkUpdate(LinkBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore[assignment]


# Database model, database table inferred from class name
class Link(LinkBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime | None = Field( # the date saved in this API
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True)  # type: ignore
    )


# Properties to return via API, id is always required
class LinkPublic(LinkBase):
    id: uuid.UUID
    created_at: datetime | None = None


class LinksPublic(SQLModel):
    data: list[LinkPublic]
    meta: dict | None = None
    

# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None
