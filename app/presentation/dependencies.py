"""FastAPI dependency injection setup.

This module is the COMPOSITION ROOT - where we wire up dependencies.

In Clean Architecture, the composition root:
1. Lives in the outermost layer (presentation/infrastructure)
2. Creates concrete implementations
3. Injects them into abstractions
4. Never imported by inner layers

This is where we decide:
=- Use UnitOfWork with SQLAlchemy (not MongoDB or Redis)
- Use Settings from environment (not hardcoded config)

All these decisions are isolated here. The application layer doesn't know
or care about these choices - it only knows about interfaces.
"""

from collections.abc import AsyncGenerator

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.application.dtos.link_dto import LinkDTO
from app.application.services.link_service import LinkService
from app.domain.repositories.token_repository import ITokenRepository
from app.domain.repositories.unit_of_work import IUnitOfWork
from app.domain.services.token_service import ITokenService
from app.infrastructure.config.settings import Settings, get_settings
from app.infrastructure.persistence.database import (
    create_database_engine,
    create_session_factory,
)
from app.infrastructure.repositories.token_repository_impl import (
    InMemoryTokenRepository,
)
from app.infrastructure.repositories.unit_of_work_impl import UnitOfWork
from app.infrastructure.security.jwt_token_service import JWTTokenService

# Module-level singletons (created once, reused throughout app lifecycle)
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None
_token_repository: ITokenRepository | None = None


def get_database_engine(settings: Settings = Depends(get_settings)) -> AsyncEngine:
    """Get or create database engine singleton.

    The engine is created once and reused for the application lifecycle.

    Args:
        settings: Application settings (injected)

    Returns:
        AsyncEngine instance
    """
    global _engine
    if _engine is None:
        _engine = create_database_engine(settings)
    return _engine


def get_session_factory(
    engine: AsyncEngine = Depends(get_database_engine),
) -> async_sessionmaker[AsyncSession]:
    """Get or create session factory singleton.

    Args:
        engine: Database engine (injected)

    Returns:
        Session factory
    """
    global _session_factory
    if _session_factory is None:
        _session_factory = create_session_factory(engine)
    return _session_factory


async def get_uow(
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
) -> AsyncGenerator[IUnitOfWork]:
    """
    Dependency that provides a Unit of Work instance.

    Now receives the session factory from get_session_factory,
    which gets its configuration from Settings.

    Dependency chain:
        get_settings() → get_database_engine() → get_session_factory() → get_uow()

    Usage:
        @app.get("/links/{link_id}")
        async def get_link(link_id: int, uow: IUnitOfWork = Depends(get_uow)):
            async with uow:
                link = await uow.links.get_by_id(link_id)
                ...

    Args:
        session_factory: Injected session factory

    Yields:
        IUnitOfWork instance
    """
    uow = UnitOfWork(session_factory)
    try:
        yield uow
    finally:
        # Cleanup if needed
        pass


def get_token_repository() -> ITokenRepository:
    """
    Dependency that provides token repository.

    This is a SINGLETON - one instance shared across the application.
    For production with multiple servers, replace with RedisTokenRepository.

    Returns:
        ITokenRepository implementation (InMemoryTokenRepository for development)

    Note:
        In production, use Redis for distributed token storage:

        def get_token_repository():
            return RedisTokenRepository(redis_client=...)
    """
    global _token_repository
    if _token_repository is None:
        _token_repository = InMemoryTokenRepository()
    return _token_repository


def get_link_service(
    session_factory: async_sessionmaker[AsyncSession] = Depends(get_session_factory),
) -> LinkService:
    """
    Dependency that provides UserService.

    The service receives:
    1. A factory function that creates UoW instances (for transaction management)
=
    Both dependencies now trace back to Settings through the dependency chain.

    Usage:
        @app.post("/links/")
        async def create_link(
            dto: CreateLinkDTO,
            service: LinkService = Depends(get_link_service)
        ):
            return await service.create_link(dto)

    Args:
        session_factory: Injected session factory (from settings)

    Returns:
        LinkService instance with all dependencies injected

    Dependency Graph:
        FastAPI endpoint
            → get_link_service()
                → get_session_factory() → get_database_engine() → Settings
    """

    def uow_factory() -> IUnitOfWork:
        return UnitOfWork(session_factory)

    return LinkService(uow_factory=uow_factory)


# Create security scheme for JWT Bearer tokens
# auto_error=False allows us to return 401 instead of 403 when credentials are missing
security = HTTPBearer(auto_error=False)


def get_token_service(
    settings: Settings = Depends(get_settings),
    token_repository: ITokenRepository = Depends(get_token_repository),
) -> ITokenService:
    """
    Dependency that provides token service.

    Returns a JWTTokenService configured with settings from environment
    and token repository for revocation tracking.

    Args:
        settings: Application settings (injected)
        token_repository: Token repository for tracking (injected)

    Returns:
        ITokenService implementation (JWTTokenService in production)
    """
    return JWTTokenService(
        secret_key=settings.secret_key,
        token_repository=token_repository,
        algorithm=settings.algorithm,
        access_token_expire_minutes=settings.access_token_expire_minutes,
        refresh_token_expire_days=settings.refresh_token_expire_days,
    )
