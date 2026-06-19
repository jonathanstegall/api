"""User repository interface."""

from abc import abstractmethod

from pydantic import AnyHttpUrl

from app.domain.entities.link import Link
from app.domain.repositories.base import IRepository


class ILinkRepository(IRepository[Link]):
    """
    Link-specific repository interface.

    Extends base repository with link-specific query methods.
    This interface defines business-driven queries like "find by email"
    which are domain concerns, not infrastructure details.
    """

    @abstractmethod
    async def get_by_url(self, url: AnyHttpUrl) -> Link | None:
        """
        Find a link by its URL.

        Args:
            link: The link URL

        Returns:
            Link if found, None otherwise
        """
        pass

    @abstractmethod
    async def url_exists(self, url: AnyHttpUrl) -> bool:
        """
        Check if a URL is already stored.

        Args:
            url: The URL to check

        Returns:
            True if URL exists, False otherwise
        """
        pass
