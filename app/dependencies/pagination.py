from fastapi import Query

class PaginationParams:
    """Offset-based pagination parameters"""

    def __init__(
        self,
        page: int = Query(
            default=1,
            ge=1,
            description="Page number (starts at 1)"
        ),
        page_size: int = Query(
            default=20,
            ge=1,
            le=100,
            alias="limit",  # Accept 'limit' as an alias
            description="Items per page (max 100)"
        )
    ):
        self.page = page
        self.page_size = page_size
        self.offset = (page - 1) * page_size

    def paginate(self, total: int) -> dict:
        """Calculate pagination metadata"""
        total_pages = (total + self.page_size - 1) // self.page_size

        return {
            "page": self.page,
            "page_size": self.page_size,
            "total_items": total,
            "total_pages": total_pages,
            "has_next": self.page < total_pages,
            "has_prev": self.page > 1
        }

