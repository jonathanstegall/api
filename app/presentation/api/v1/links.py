"""Link API endpoints."""

import uuid
from fastapi import APIRouter, Depends, status

from app.application.dtos.link_dto import CreateLinkDTO, UpdateLinkDTO, LinkDTO
from app.application.services.link_service import LinkService
from app.presentation.dependencies import get_link_service

router = APIRouter(prefix="/links", tags=["links"])


@router.post(
    "/",
    response_model=LinkDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new link",
    description="Create a new link with URL and title.",
)
async def create_link(
    dto: CreateLinkDTO,
    service: LinkService = Depends(get_link_service),
) -> LinkDTO:
    """
    Create a new link.

    Exception handling is done by global exception handlers.
    The service layer raises domain/application exceptions,
    which are automatically converted to appropriate HTTP responses.
    """
    return await service.create_link(dto)


@router.get(
    "/{link_id}",
    response_model=LinkDTO,
    summary="Get link by ID",
    description="Retrieve a link by its ID.",
)
async def get_link(
    link_id: int,
    service: LinkService = Depends(get_link_service),
) -> LinkDTO:
    """Get link by ID."""
    return await service.get_link_by_id(link_id)


@router.get(
    "/",
    response_model=list[LinkDTO],
    summary="Get all links",
    description="Retrieve all links with optional pagination.",
)
async def get_links(
    skip: int = 0,
    limit: int = 100,
    service: LinkService = Depends(get_link_service),
) -> list[LinkDTO]:
    """Get all links with pagination."""
    return await service.get_all_links(skip=skip, limit=limit)


@router.put(
    "/{link_id}",
    response_model=LinkDTO,
    summary="Update link",
    description="Update link information (URL and/or title).",
)
async def update_link(
    link_id: str,
    dto: UpdateLinkDTO,
    service: LinkService = Depends(get_link_service),
) -> LinkDTO:
    """Update link."""
    return await service.update_link(link_id, dto)


@router.delete(
    "/{link_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete link",
    description="Delete a link by its ID.",
)
async def delete_link(
    link_id: str,
    service: LinkService = Depends(get_link_service),
) -> None:
    """Delete link."""
    await service.delete_link(link_id)
