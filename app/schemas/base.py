from pydantic import (
    BaseModel,
    ConfigDict,
)
from typing import TypeVar, Generic

T = TypeVar("T")

class BaseSchema(BaseModel, Generic[T]):
    model_config = ConfigDict(
        from_attributes=True,
        arbitrary_types_allowed=True
    )
