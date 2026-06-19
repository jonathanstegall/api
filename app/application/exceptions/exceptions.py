"""Application layer exceptions."""


class ApplicationError(Exception):
    """Base application layer exception."""

    def __init__(self, message: str, error_code: str = "APPLICATION_ERROR"):
        """
        Initialize application exception.

        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
        """
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class LinkNotFoundError(ApplicationError):
    """Raised when a link is not found."""

    def __init__(self, message: str = "Link not found"):
        super().__init__(message, error_code="LINK_NOT_FOUND")


class LinkAlreadyExistsError(ApplicationError):
    """Raised when attempting to create a link with existing source ID and source combination."""

    def __init__(self, message: str = "Link already exists"):
        super().__init__(message, error_code="LINK_ALREADY_EXISTS")


class InvalidCredentialsError(ApplicationError):
    """Raised when login credentials are invalid."""

    def __init__(self, message: str = "Invalid credentials"):
        super().__init__(message, error_code="INVALID_CREDENTIALS")


class TokenExpiredError(ApplicationError):
    """Raised when a token has expired."""

    def __init__(self, message: str = "Token has expired"):
        super().__init__(message, error_code="TOKEN_EXPIRED")


class InvalidTokenError(ApplicationError):
    """Raised when a token is invalid or malformed."""

    def __init__(self, message: str = "Invalid token"):
        super().__init__(message, error_code="INVALID_TOKEN")


class UnauthorizedError(ApplicationError):
    """Raised when user is not authenticated."""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(message, error_code="UNAUTHORIZED")