from typing import Annotated, Literal

from fastapi import FastAPI, Query, Request
from pydantic import BaseModel, Field, TypeAdapter, field_validator, model_validator

from app.config import config

app = FastAPI()


class RequestParameters(BaseModel):
    page: int | None = 1
    page_size: int | None = config.page_size
    order_by: str | None = None
    search: str | None = ""

    #@field_validator('page')
    #def check_page(cls, v):
    #    if isinstance(v, str): 
    #         print('it is a string')
    #    else:
    #        print(f'value is {v}')
    #    return v
    
    #@field_validator('number_of_pages')
    #def total_pages(cls, v):
    #    if cls.number_of_pages is 0 and cls.total is not None:
    #        cls.number_of_pages = cls.total / cls.page_size
    #    return cls

    #@model_validator(mode='after')
    #def set_default_pages(self):
    #  if self.number_of_pages is None and self.total is not None:
    #    self.numer_of_pages = self.total / self.page_size
    #  return self