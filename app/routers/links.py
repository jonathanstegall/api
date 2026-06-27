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


router = APIRouter(prefix="/links")


@router.get("/", response_model=LinkSchema)
async def get_link(
    id: uuid.UUID,
    session: Session = Depends(create_session),
) -> LinkSchema:
    """Get link by ID."""

    return LinkService(session).get_link(id)


@router.get("/links/", response_model=List[LinkSchema])
async def get_links(
    url: str,
    source: str,
    session: Session = Depends(create_session),
) -> List[LinkSchema]:
    """Get links by ``url`` and ``source``."""

    return LinkService(session).get_links(url, source)
