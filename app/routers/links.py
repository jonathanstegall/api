import uuid
from typing import Any

from fastapi import (
    APIRouter,
    Depends,
)
from sqlalchemy.orm import Session

from app.backend.database.session import create_session
from app.dependencies.parameters import RequestParameters
from app.schemas.response import Response
from app.schemas.links import LinkSchema
from app.services.links import LinkService

from app.exceptions import AppError, HTTPExceptionFromAppError

router = APIRouter()

@router.get("/links/")
async def get_links(params: RequestParameters = Depends(), session: Session = Depends(create_session)):
    """Get multiple links."""
    service = LinkService(session)
    try:
        result = service.get_links(params)
        return result
    except AppError as e:
        raise HTTPExceptionFromAppError(e) from e

@router.get("/link/", response_model=Response[LinkSchema])
async def get_link(
    id: uuid.UUID | None = None,
    url: str | None = None,
    params: RequestParameters = Depends(),
    session: Session = Depends(create_session),
) -> Response[LinkSchema]:
    """Get a single link."""
    service = LinkService(session)
    try:
        result = service.get_link(id, url, params)
        return result
    except AppError as e:
        raise HTTPExceptionFromAppError(e) from e

@router.post("/links/ingest")
async def ingest_links(
    sources: str,
    params: RequestParameters = Depends(),
    session: Session = Depends(create_session),
):
    """Ingest links from an API."""
    service = LinkService(session)
    try:
        result = service.ingest_links(sources, params)
        return result
    except AppError as e:
        raise HTTPExceptionFromAppError(e) from e
