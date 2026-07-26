from pydantic import BaseModel
from typing import TypeVar, Generic, Optional

T = TypeVar("T")

class Response(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""
    items: list[T]
    total: Optional[int]
    number_of_pages: Optional[int]
    page: Optional[int]
    page_size: Optional[int]

    @classmethod
    def wrap(cls, items: list, total: int, page: int, page_size: int | None = None, number_of_pages: int | None = None, next_page: str | None = None, previous_page: str | None = None) -> "Response[T]":

        number_of_pages = cls.get_number_of_pages(total, page_size)

        #next_page = ""
        #next_page = cls.get_next_page(page, number_of_pages)
        #previous_page = ""

        return cls(
            items = items,
            total = total,
            page = page,
            page_size = page_size,
            number_of_pages = number_of_pages,
            #next_page = next_page,
            #previous_page = previous_page
        )

    @classmethod
    def get_number_of_pages(cls, total: int, page_size: int) -> int:
        rest = total % page_size
        quotient = total // page_size
        return quotient if not rest else quotient + 1
