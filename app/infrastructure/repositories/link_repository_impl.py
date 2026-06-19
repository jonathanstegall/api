"""Link repository implementation using SQLAlchemy."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from pydantic import AnyHttpUrl

from app.domain.entities.link import Link
from app.domain.repositories.link_repository import ILinkRepository
from app.infrastructure.persistence.models.link_model import LinkModel


class LinkRepository(ILinkRepository):
    """
    SQLAlchemy implementation of ILinkRepository.

    This class contains all database-specific code and depends on:
    - SQLAlchemy (infrastructure)
    - LinkModel (infrastructure ORM mapping)

    It implements the ILinkRepository interface (domain) and returns
    domain entities, never exposing ORM models to the application layer.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with a database session.

        Args:
            session: SQLAlchemy async session (managed by UoW)
        """
        self._session = session

    async def get_by_id(self, id: int) -> Link | None:
        """Get link by ID."""
        result = await self._session.execute(
            select(LinkModel).where(LinkModel.id == id)
        )
        link_model = result.scalar_one_or_none()

        if link_model is None:
            return None

        return link_model.to_entity()

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[Link]:
        """Get all links with pagination."""
        result = await self._session.execute(
            select(LinkModel).offset(skip).limit(limit)
        )
        link_models = result.scalars().all()

        return [model.to_entity() for model in link_models]

    async def add(self, entity: Link) -> Link:
        """
        Add a new link.

        Note: We convert domain entity -> ORM model, persist it,
        then convert back to domain entity.
        """
        link_model = LinkModel.from_entity(entity)

        self._session.add(link_model)
        await self._session.flush()  # Get generated ID without committing
        await self._session.refresh(link_model)  # Refresh timestamps

        return link_model.to_entity()

    async def update(self, entity: Link) -> Link:
        """
        Update existing link.

        Note: The repository is responsible for managing the updated_at timestamp.
        This keeps the domain layer pure by moving infrastructure concerns here.
        """
        if entity.id is None:
            raise ValueError("Cannot update link without ID")

        # Get existing model
        result = await self._session.execute(
            select(LinkModel).where(LinkModel.id == entity.id)
        )
        link_model = result.scalar_one_or_none()

        if link_model is None:
            raise ValueError(f"Link with ID {entity.id} not found")

        # Update fields from entity
        link_model.url = entity.url
        link_model.title = entity.title
        link_model.source = entity.source
        link_model.source_id = entity.source_id
        link_model.type = entity.type
        link_model.date = entity.date
        link_model.creator = entity.creator
        link_model.referrer = entity.referrer
        link_model.text = entity.text
        link_model.saved_date = entity.saved_date
        link_model.format = entity.format
        link_model.updated_at = func.now()

        await self._session.flush()
        await self._session.refresh(link_model)

        return link_model.to_entity()

    async def delete(self, id: int) -> bool:
        """Delete link by ID."""
        result = await self._session.execute(
            select(LinkModel).where(LinkModel.id == id)
        )
        link_model = result.scalar_one_or_none()

        if link_model is None:
            return False

        await self._session.delete(link_model)
        await self._session.flush()

        return True

    async def exists(self, id: int) -> bool:
        """Check if link exists."""
        result = await self._session.execute(
            select(LinkModel.id).where(LinkModel.id == id)
        )
        return result.scalar_one_or_none() is not None

    async def get_by_url(self, url: AnyHttpUrl) -> Link | None:
        """Get link by URL."""
        result = await self._session.execute(
            select(LinkModel).where(LinkModel.url == url)
        )
        link_model = result.scalar_one_or_none()

        if link_model is None:
            return None

        return link_model.to_entity()

    async def url_exists(self, url: AnyHttpUrl) -> bool:
        """Check if URL is already saved."""
        result = await self._session.execute(
            select(LinkModel.id).where(LinkModel.url == url)
        )
        return result.scalar_one_or_none() is not None
