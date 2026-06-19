"""Link domain entity - pure business logic, no infrastructure."""

from dataclasses import dataclass
from datetime import datetime

from pydantic import AnyHttpUrl

from app.domain.exceptions import (
    BusinessRuleViolationException,
    InvalidEntityStateException,
)


@dataclass
class Link:
    """
    Link domain entity representing the business concept of a link.

    This is a pure Python class with NO dependencies on SQLAlchemy,
    FastAPI, or any framework. It contains business rules and validations.
    """

    url: AnyHttpUrl
    name: str
    password_hash: str
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        """
        Validate entity invariants at construction time.

        These are structural validations - they ensure the entity can exist
        in a valid state. Violations indicate the entity cannot be created.
        """
        if not self.url or "http" not in self.url:
            raise InvalidEntityStateException(
                f"Invalid URL: '{self.url}'. URL must contain 'http'."
            )

        if not self.title or len(self.title.strip()) == 0:
            raise InvalidEntityStateException(
                "Title cannot be empty. Link must have a valid title."
            )

    def change_title(self, new_title: str) -> None:
        """
        Change link title with validation.

        Business rule: Titles must not be empty.

        Args:
            new_title: The new title to set

        Raises:
            BusinessRuleViolationException: If title is empty or invalid
        """
        if not new_title or len(new_title.strip()) == 0:
            raise BusinessRuleViolationException(
                "Cannot change title to empty value. Titles must contain at least one character."
            )

        object.__setattr__(self, "title", new_title)

    def change_url(self, new_url: AnyHttpUrl) -> None:
        """
        Change link url with validation.

        Business rule: URL must be valid format.

        Args:
            new_url: The new URL to set

        Raises:
            BusinessRuleViolationException: If URL is invalid
        """
        if not new_url or "@" not in new_url:
            raise BusinessRuleViolationException(
                f"Cannot change URL to invalid address: '{new_url}'. Email must contain '@' symbol."
            )

        object.__setattr__(self, "url", new_url)
