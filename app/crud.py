import uuid
from typing import Any

from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from app.models import Link, LinkCreate

def create_link(*, session: Session, link_create: LinkCreate) -> Link:
    db_link = Link.model_validate(link_create)
    try:
        session.add(db_link)
        session.commit()
        session.refresh(db_link)
        return db_link
    except IntegrityError as e:
        session.rollback()
        if "source_id" in str(e.orig):
            raise ValueError("This item already exists")
        raise ValueError("Unique constraint violation")


def get_link_by_url(*, session: Session, url: str) -> Link | None:
    statement = select(Link).where(Link.url == url)
    session_link = session.exec(statement).first()
    return session_link

