from app.schemas.base import BaseSchema

class Pagination(BaseSchema):
    """Pydantic model for paginated results."""
    itemsPerPage: int
    page: int
    total: int
