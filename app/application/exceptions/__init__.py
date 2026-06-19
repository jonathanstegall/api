"""Application layer exceptions."""

from app.application.exceptions.exceptions import (
    ApplicationError,
    LinkAlreadyExistsError,
    LinkNotFoundError,
)

__all__ = ["ApplicationError", "LinkNotFoundError", "LinkAlreadyExistsError"]