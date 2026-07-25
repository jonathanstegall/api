import uuid
from typing import List

from sqlalchemy import select

from app.backend.cache.cache import get_schema, set_schema, cache_key_builder

from app.models.links import LinkModel
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
    

    def get_links(self, offset: int = 0, limit: int = 100) -> List[LinkSchema]:
        """Select links with values for offset and limit."""

        return LinkDataManager(self.session).get_links(offset, limit)

    
    def get_link(self, id: uuid.UUID | None = None, url: str | None = None) -> LinkSchema:
        """Get link by ID."""

        key = cache_key_builder(self, id=id, url=url)

        cached = get_model(key, LinkModel)
        if cached:
            return cached

        link = LinkDataManager(self.session).get_link(id, url)

        set_model(key, link)
        return link

    


class LinkDataManager(BaseDataManager):

    def add_link(self, link: LinkModel) -> None:
        """Write link to database."""

        self.add_one(link)


    def get_links(self, offset: int, limit: int) -> List[LinkSchema]:
        schemas: List[LinkSchema] = list()

        stmt = select(LinkModel).offset(offset).limit(limit)

        for model in self.get_all(stmt):
            schemas += [LinkSchema(**model.to_dict())]

        return schemas
    

    def get_link(self, id: uuid.UUID | None = None, url: str | None = None) -> LinkSchema:
        stmt = select(LinkModel).where(LinkModel.id == id)
        model = self.get_one(stmt)

        return LinkSchema(**model.to_dict())

    
