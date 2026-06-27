from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine, URL
from sqlalchemy.orm import (
    Session,
    sessionmaker,
)

from app.config import config

url_object = URL.create(
    config.database.dialect,
    username=config.database.user,
    password=config.database.password,
    host=config.database.host,
    port=config.database.port,
    database=config.database.name
)

# create session factory to generate new database sessions
SessionFactory = sessionmaker(
    bind=create_engine(url_object),
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


def create_session() -> Iterator[Session]:
    """Create new database session.

    Yields:
        Database session.
    """

    session = SessionFactory()

    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def open_session() -> Iterator[Session]:
    """Create new database session with context manager.

    Yields:
        Database session.
    """

    return create_session()
