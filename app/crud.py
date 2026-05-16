import uuid
from typing import Any

from sqlmodel import Session, select

from app.models import Link, LinkCreate

# Dummy hash to use for timing attack prevention when user is not found
# This is an Argon2 hash of a random password, used to ensure constant-time comparison
DUMMY_HASH = "$argon2id$v=19$m=65536,t=3,p=4$MjQyZWE1MzBjYjJlZTI0Yw$YTU4NGM5ZTZmYjE2NzZlZjY0ZWY3ZGRkY2U2OWFjNjk"

def create_link(*, session: Session, link_in: LinkCreate) -> Link:
    db_link = Link.model_validate(link_in)
    session.add(db_link)
    session.commit()
    session.refresh(db_link)
    return db_link
