import uuid
from typing import List, Annotated

from sqlalchemy import select

from app.backend.cache.cache import get_schema, set_schema, cache_key_builder

from app.models.links import LinkModel
from app.dependencies.parameters import RequestParameters
from app.schemas.response import Response
from app.schemas.links import CreateLinkSchema, LinkSchema
from app.services.base import (
    BaseDataManager,
    BaseService,
)


class LinkService(BaseService):

    def create_link(self, user: CreateLinkSchema) -> None:
        """Add link entry to database."""

        link_model = LinkModel(
            name=user.name,
            email=user.email,
            hashed_password=self.bcrypt(user.password),
        )

        LinkDataManager(self.session).add_link(link_model)
    

    def get_links(self, params) -> Response[LinkSchema]:
        """Select links with values for offset and limit."""

        offset = (params.page - 1) * params.page_size
        limit = params.page_size

        if params.saved_date_start is not None and params.saved_date_end is not None:
            base_statement = select(LinkModel).where(LinkModel.saved_date.between(params.saved_date_start, params.saved_date_end))
        else:
            base_statement = select(LinkModel)

        statement = base_statement.offset(offset).limit(limit)

        links = LinkDataManager(self.session).get_links(base_statement, statement, params)

        return links

    
    def get_link(self, id: uuid.UUID | None = None, url: str | None = None, params: RequestParameters | None = None) -> Response[LinkSchema]:
        """Get link by ID."""

        if id is not None:
            link = LinkDataManager(self.session).get_link("id", id, params)
        elif url is not None:
            link = LinkDataManager(self.session).get_link("url", url, params)

        return link


    def ingest_links(self, sources, params: RequestParameters | None = None):
        sources = sources.split(",")
        return {"sources": sources}


class LinkDataManager(BaseDataManager):

    def add_link(self, link: LinkModel) -> None:
        """Write link to database."""

        self.add_one(link)


    def get_links(self, base_statement, statement, params: RequestParameters | None = None) -> Response[LinkSchema]:
        schemas: List[LinkSchema] = list()        
        for model in self.get_all(statement):
            schemas += [LinkSchema(**model.to_dict())]

        count = self.count(base_statement)
        return Response.wrap(items=schemas, total=count, page=params.page, page_size=params.page_size)
    

    def get_link(self, field, value, params: RequestParameters | None = None) -> Response[LinkSchema]:
        statement = select(LinkModel).where(getattr(LinkModel, field) == value)
        model = self.get_one(statement)

        count = self.count(statement)
        return Response.wrap(items=[LinkSchema(**model.to_dict())], total=count, page=params.page, page_size=params.page_size)

    
