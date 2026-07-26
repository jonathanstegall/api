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

        links = LinkDataManager(self.session).get_links(params)

        return links

    
    def get_link(self, id: uuid.UUID | None = None, url: str | None = None, params: RequestParameters | None = None) -> Response[LinkSchema]:
        """Get link by ID."""

        link = LinkDataManager(self.session).get_link(id, url, params)
        return link


class LinkDataManager(BaseDataManager):

    def add_link(self, link: LinkModel) -> None:
        """Write link to database."""

        self.add_one(link)


    def get_links(self, params) -> Response[LinkSchema]:
        offset = (params.page - 1) * params.page_size
        limit = params.page_size

        schemas: List[LinkSchema] = list()
        stmt = select(LinkModel).offset(offset).limit(limit)

        for model in self.get_all(stmt):
            schemas += [LinkSchema(**model.to_dict())]

        #return schemas
        count = self.count(select(LinkModel))
        return Response.wrap(items=schemas, total=count, page=params.page, page_size=params.page_size)
    

    def get_link(self, id: uuid.UUID | None = None, url: str | None = None, params: RequestParameters | None = None) -> Response[LinkSchema]:
        stmt = select(LinkModel).where(LinkModel.id == id)
        model = self.get_one(stmt)
        count = self.count(stmt)
        
        #return LinkSchema(**model.to_dict())
        return Response.wrap(items=[LinkSchema(**model.to_dict())], total=count)

    
