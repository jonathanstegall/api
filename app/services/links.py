import uuid
from typing import List

from sqlalchemy import select

from app.backend.cache.cache import get_model, set_model, cache_key_record

from app.models.links import LinkModel
from app.schemas.links import LinkSchema
from app.services.base import (
    BaseDataManager,
    BaseService,
)


class LinkService(BaseService):
    def get_link(self, id: uuid.UUID) -> LinkSchema:
        """Get link by ID."""

        key = cache_key_record("link", id)

        cached = get_model(key, LinkModel)
        if cached:
            return cached

        link = LinkDataManager(self.session).get_link(id)

        set_model(key, link)

        return LinkDataManager(self.session).get_link(id)

    def get_links(self, url: str, source: str) -> List[LinkSchema]:
        """Select links with filter by ``url`` and ``source``."""

        return LinkDataManager(self.session).get_links(url, source)


class LinkDataManager(BaseDataManager):
    def get_link(self, id: uuid.UUID) -> LinkSchema:
        stmt = select(LinkModel).where(LinkModel.id == id)
        model = self.get_one(stmt)

        return LinkSchema(**model.to_dict())

    def get_links(self, url: str, source: str) -> List[LinkSchema]:
        schemas: List[LinkSchema] = list()

        stmt = select(LinkModel).where(
            LinkModel.url == url,
            LinkModel.source == source,
        )

        for model in self.get_all(stmt):
            schemas += [LinkSchema(**model.to_dict())]

        return schemas
