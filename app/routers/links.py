import uuid
from typing import List

from fastapi import (
    APIRouter,
    Depends,
)
from sqlalchemy.orm import Session

from app.backend.database.session import create_session

#from app.const import (
#    MOVIES_TAGS,
#    MOVIES_URL,
#    MOVIES_URL_NEW,
#)
from app.schemas.links import LinkSchema
from app.services.links import LinkService


router = APIRouter()


@router.get("/links/", response_model=List[LinkSchema])
async def get_links(
    offset: int = 0,
    limit: int = 100,
    session: Session = Depends(create_session),
) -> List[LinkSchema]:
    """Get multiple links."""

    return LinkService(session).get_links(offset, limit)


@router.get("/link/", response_model=LinkSchema)
async def get_link(
    id: uuid.UUID | None = None,
    url: str | None = None,
    session: Session = Depends(create_session),
) -> LinkSchema:
    """Get a single link."""

    return LinkService(session).get_link(id, url)
