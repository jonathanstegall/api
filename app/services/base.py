from typing import (
    Any,
    List,
    Sequence,
    Type,
)

from sqlalchemy import (
    func,
    select,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import Executable

from app.models.base import SQLModel
from app.exceptions import DatabaseError, DatabaseConstraintError


class SessionMixin:
    """Provides instance of database session."""

    def __init__(self, session: Session) -> None:
        self.session = session


class BaseService(SessionMixin):
    """Base class for application services."""

    def __init__(self, session: Session):
        super().__init__(session)

    def _handle_database_constraint_error(self, constraint_error: DatabaseConstraintError, *, source: str | None = None, extra_details: dict | None = None) -> None:
        """Handle database constraint violation by raising AppError.

        This method converts DatabaseConstraintError (unique constraint violation) to
        ConflictError (an AppError), returning proper JSON error details. The router layer
        will convert ConflictError → HTTPExceptionFromAppError with HTTP 409.

        Args:
            constraint_error: The DatabaseConstraintError raised by BaseDataManager.
            source: Optional source identifier (e.g., "instapaper").
            extra_details: Optional additional details to include in error details.
        """
        from app.exceptions import ConflictError
        conflict_error = ConflictError(
            "Duplicate record detected",
            details={
                "constraint_error": str(constraint_error),
                "source": source,
                **(extra_details or {})
            },
        )
        raise conflict_error from constraint_error




class BaseDataManager(SessionMixin):
    """Base data manager class responsible for operations over database."""

    def add_one(self, model: Any) -> None:
        try:
            self.session.add(model)
            # Commit immediately to detect IntegrityError (unique constraint violation)
            self.session.commit()
        except IntegrityError as e:
            self.session.rollback()
            raise DatabaseConstraintError(f"Failed to add model due to unique constraint violation: {e}", operation="add_one") from e
        except Exception as e:
            # Rollback on error
            self.session.rollback()
            raise DatabaseError(f"Failed to add model: {e}", operation="add_one") from e

    def add_all(self, models: Sequence[Any]) -> None:
        try:
            self.session.add_all(models)
            # Commit immediately to detect IntegrityError (unique constraint violation)
            self.session.commit()
        except IntegrityError as e:
            self.session.rollback()
            raise DatabaseConstraintError(f"Failed to add models due to unique constraint violation: {e}", operation="add_all") from e
        except Exception as e:
            # Rollback on error
            self.session.rollback()
            raise DatabaseError(f"Failed to add models: {e}", operation="add_all") from e

    def count(self, query: Executable) -> Any:
        # In SQLAlchemy 2.0, query might be a Select object with modifiers (offset/limit).
        # Use .subquery() to convert it to a subquery that can be used as a FROM clause.
        subq = query.subquery()
        from sqlalchemy import func
        result = self.session.execute(select(func.count()).select_from(subq))
        return result.scalar()



    def get_one(self, select_stmt: Executable) -> Any:
        try:
            result = self.session.scalar(select_stmt)
            return result
        except Exception as e:
            self.session.rollback()  # already committed elsewhere
            raise DatabaseError(f"Failed to get one: {e}", operation="get_one") from e

    def get_all(self, select_stmt: Executable) -> List[Any]:
        try:
            result = list(self.session.scalars(select_stmt).all())
            return result
        except Exception as e:
            self.session.rollback() # already committed elsewhere
            raise DatabaseError(f"Failed to get all: {e}", operation="get_all") from e

    def get_from_tvf(self, model: Type[SQLModel], *args: Any) -> List[Any]:
        """Query from table valued function.

        This is a wrapper function that can be used to retrieve data from
        table valued functions.

        Examples:
            from app.models.base import SQLModel

            class MyModel(SQLModel):
                __tablename__ = "function"
                __table_args__ = {"schema": "schema"}

                x: Mapped[int] = mapped_column("x", primary_key=True)
                y: Mapped[str] = mapped_column("y")
                z: Mapped[float] = mapped_column("z")

            # equivalent to "SELECT x, y, z FROM schema.function(1, 'AAA')"
            BaseDataManager(session).get_from_tvf(MyModel, 1, "AAA")
        """

        return self.get_all(self.select_from_tvf(model, *args))


    @staticmethod
    def select_from_tvf(model: Type[SQLModel], *args: Any) -> Executable:
        fn = getattr(getattr(func, model.schema()), model.table_name())
        stmt = select(fn(*args).table_valued(*model.fields()))
        return select(model).from_statement(stmt)

