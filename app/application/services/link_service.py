"""Link service - application layer business logic."""

from collections.abc import Callable

from app.application.dtos.link_dto import CreateLinkDTO, UpdateLinkDTO, LinkDTO
from app.application.exceptions import (
    LinkAlreadyExistsError,
    LinkNotFoundError,
)
from app.domain.entities.link import Link
from app.domain.repositories.unit_of_work import IUnitOfWork
#from app.domain.services.password_hasher import IPasswordHasher


class LinkService:
    """
    Link service encapsulating link-related use cases.

    This service:
    1. Depends on IUnitOfWork abstraction (not concrete implementation)
    2. Depends on IPasswordHasher abstraction (not concrete implementation)
    3. Contains business logic and orchestration
    4. Uses domain entities internally
    5. Returns DTOs to the presentation layer

    Dependency Inversion Principle:
    - LinkService (high-level) depends on IPasswordHasher (abstraction)
    - Argon2PasswordHasher (low-level) implements IPasswordHasher
    - Dependencies point INWARD toward the domain layer
    """

    def __init__(
        self,
        uow_factory: Callable[[], IUnitOfWork],
#        password_hasher: IPasswordHasher,
    ):
        """
        Initialize service with dependencies.

        Args:
            uow_factory: Factory function that returns IUnitOfWork instances
            password_hasher: Password hashing service (abstraction, not concrete class)

        Example:
            # Production
            service = LinkService(
                uow_factory=lambda: UnitOfWork(session),
                password_hasher=Argon2PasswordHasher()
            )

            # Testing
            service = LinkService(
                uow_factory=lambda: FakeUnitOfWork(),
                password_hasher=FakePasswordHasher()
            )
        """
        self._uow_factory = uow_factory
        #self._password_hasher = password_hasher

    async def create_link(self, dto: CreateLinkDTO) -> LinkDTO:
        """
        Create a new link.

        Business rules:
        1. 

        Args:
            dto: Link creation data

        Returns:
            Created link DTO

        Raises:
            LinkAlreadyExistsError: If source/source ID already exists
        """
        async with self._uow_factory() as uow:
            # Check if email already exists
            if await uow.links.source_item_exists(dto.source, dto.source_id):
                raise LinkAlreadyExistsError(f"Link {dto.source} {dto.source_id} already saved")

            # Create domain entity with hashed password
            link = Link(
                url=dto.url,
                title=dto.title,
                #password_hash=self._password_hasher.hash(dto.password),
            )

            # Persist via repository
            created_link = await uow.links.add(link)

            # Commit transaction
            await uow.commit()

            # Return DTO
            return LinkDTO.from_entity(created_link)

    async def get_link_by_id(self, link_id: int) -> LinkDTO:
        """
        Retrieve link by ID.

        Args:
            link_id: Link ID

        Returns:
            Link DTO

        Raises:
            LinkNotFoundError: If link doesn't exist
        """
        async with self._uow_factory() as uow:
            link = await uow.links.get_by_id(link_id)

            if link is None:
                raise LinkNotFoundError(f"Link with ID {link_id} not found")

            return LinkDTO.from_entity(link)

    async def get_link_by_url(self, url: str) -> LinkDTO | None:
        """
        Get link by url.

        Args:
            url: Link URL

        Returns:
            Link DTO if found, None otherwise
        """
        async with self._uow_factory() as uow:
            link = await uow.links.get_by_url(url)

            if link is None:
                return None

            return LinkDTO.from_entity(link)
        
    async def get_link_by_source_and_id(self, source: str, source_id: str) -> LinkDTO | None:
        """
        Get link by source and source ID.

        Args:
            source: source of link
            source_id: ID of item at source

        Returns:
            Link DTO if found, None otherwise
        """
        async with self._uow_factory() as uow:
            link = await uow.links.get_by_source_and_id(source, source_id)

            if link is None:
                return None

            return LinkDTO.from_entity(link)

    async def get_all_links(self, skip: int = 0, limit: int = 100) -> list[LinkDTO]:
        """
        Get all links with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of link DTOs
        """
        async with self._uow_factory() as uow:
            links = await uow.links.get_all(skip=skip, limit=limit)
            return [LinkDTO.from_entity(link) for link in links]

    async def update_link(self, link_id: int, dto: UpdateLinkDTO) -> LinkDTO:
        """
        Update link information.

        Args:
            link_id: Link ID to update
            dto: Update data

        Returns:
            Updated link DTO

        Raises:
            LinkNotFoundError: If link doesn't exist
            LinkAlreadyExistsError: If source and source ID combo is taken by another link
        """
        async with self._uow_factory() as uow:
            # Get existing link
            link = await uow.links.get_by_id(link_id)
            if link is None:
                raise LinkNotFoundError(f"Link with ID {link_id} not found")

            # Check email uniqueness if changing
            if dto.source and dto.source != link.source:
                existing = await uow.links.get_by_source_and_id(dto.source, dto.source_id)
                if existing is not None:
                    raise LinkAlreadyExistsError(f"Link {dto.source, dto.source_id} already in use")

            # Update entity using domain methods
            #if dto.name:
            #    link.change_name(dto.name)

            #if dto.email:
            #    link.change_email(dto.email)

            # Persist changes
            updated_link = await uow.linkd.update(link)

            # Commit
            await uow.commit()

            return LinkDTO.from_entity(updated_link)

    async def delete_link(self, link_id: int) -> None:
        """
        Delete a link.

        Args:
            link_id: Link ID to delete

        Raises:
            LinkNotFoundError: If link doesn't exist
        """
        async with self._uow_factory() as uow:
            deleted = await uow.links.delete(link_id)

            if not deleted:
                raise LinkNotFoundError(f"Link with ID {link_id} not found")

            await uow.commit()
