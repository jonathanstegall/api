import uuid
from typing import Any

from fastapi import (APIRouter, Depends, Request)
from sqlalchemy.orm import Session

from app.backend.database.session import create_session
from app.dependencies.parameters import RequestParameters, IngestionParameters
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
):
    """Get a single link."""
    service = LinkService(session)
    try:
        result = service.get_link(id, url, params)
        return result
    except AppError as e:
        raise HTTPExceptionFromAppError(e) from e


@router.post("/links/ingest")
async def ingest(request: Request,
    params: IngestionParameters = None,
    session: Session = Depends(create_session),
):
    """Ingest links from an API."""
    query_params = request.query_params

    # Get sources from the current query value for `sources` or keys that have the source name in them
    query_sources = query_params.get("sources", "")
    if not query_sources:
        # Infer sources from source-prefixed query keys (e.g., instapaper.limit)
        sources_found = set()
        for key in query_params.keys():
            if "." in key:
                source_name = key.split(".")[0]
                sources_found.add(source_name)
        if not sources_found:
            raise HTTPExceptionFromAppError("Missing `sources` parameter")
        sources_list = list(sources_found)
    else:
        sources_list = [s.strip() for s in query_sources.split(",")]

    # Parse general params (page, page_size, order_by, search, saved_date_start, saved_date_end)
    # from query (without prefix)
    general_params = {}
    for field in ["page", "page_size", "order_by", "search", "saved_date_start", "saved_date_end"]:
        val = query_params.get(field)
        if val is not None:
            general_params[field] = val

    # Parse source-specific params (e.g., "instapaper.limit") into source_options
    source_options = {}
    for key, value in query_params.items():
        if key == "sources":
            continue
        if "." in key:
            source_name, param_name = key.split(".", 1)
            if source_name in sources_list:
                source_options.setdefault(source_name, {})[param_name] = value

    # Create IngestionParameters
    if params is not None:
        # Merge source_options into params.source_options if it exists
        if params.source_options is None:
            params.source_options = {}
        params.source_options.update(source_options)
        # Merge general params (page, page_size, etc.) from query
        for field, val in general_params.items():
            if hasattr(params, field):
                setattr(params, field, val)
    else:
        params = IngestionParameters(source_options=source_options, **general_params)

    # ensure source list is unique
    seen = set()
    unique_sources = []
    for s in sources_list:
        if s not in seen:
            seen.add(s)
            unique_sources.append(s)
    sources_list = unique_sources

    # pass data to the link service
    service = LinkService(session)
    try:
        result = service.ingest(sources_list, params)
        return result
    except AppError as e:
        raise HTTPExceptionFromAppError(e) from e
