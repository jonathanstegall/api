import uuid
from typing import List

from fastapi import (
    APIRouter,
    Depends,
)
from sqlalchemy.orm import Session

from app.backend.database.session import create_session
from app.dependencies.parameters import RequestParameters

#from app.const import (
#    MOVIES_TAGS,
#    MOVIES_URL,
#    MOVIES_URL_NEW,
#)
from app.schemas.response import Response
from app.schemas.links import LinkSchema
from app.services.links import LinkService


router = APIRouter()

@router.get("/links/")
async def get_links(params: RequestParameters = Depends(), session: Session = Depends(create_session)):
    """Get multiple links."""
    links = LinkService(session).get_links(params)
    return links


@router.get("/link/", response_model=Response[LinkSchema])
async def get_link(
    id: uuid.UUID | None = None,
    url: str | None = None,
    params: RequestParameters = Depends(),
    session: Session = Depends(create_session),
) -> LinkSchema:
    """Get a single link."""
    link = LinkService(session).get_link(id, url, params)
    return link


@router.post("/links/ingest")
async def get_links(
    sources: str,
    params: RequestParameters = Depends(),
    session: Session = Depends(create_session)
    ):
    """Ingest links from a source."""
    links = LinkService(session).ingest_links(sources, params)
    return links

