import uuid
from typing import List

from sqlalchemy import select

from app.config import config

from app.backend.ingest.tumblr import Tumblr
from app.backend.ingest.instapaper import Instapaper
from app.backend.ingest.raindrop import Raindrop

from app.models.links import LinkModel
from app.dependencies.parameters import RequestParameters, IngestionParameters
from app.schemas.response import Response
from app.schemas.links import CreateLinkSchema, LinkSchema
from app.services.base import (
    BaseDataManager,
    BaseService,
)

from app.exceptions import (DatabaseConstraintError, DatabaseError, NotFoundError, ParamValidationError, BadRequestError)


class LinkService(BaseService):

    def create_link(self, user: CreateLinkSchema) -> None:
        """Add link entry to database."""

        link_model = LinkModel(
            name=user.name,
            email=user.email,
            hashed_password=self.bcrypt(user.password),
        )

        LinkDataManager(self.session).add_link(link_model)


    def create_links(self, links: List[CreateLinkSchema]) -> None:
        """Bulk add link entries to database."""

        link_models = [LinkModel(**_.model_dump()) for _ in links]
        #self.session.add_all(link_models)
        LinkDataManager(self.session).add_links(link_models)


    def get_links(self, params) -> Response[LinkSchema]:
        """Select links with values for offset and limit."""

        offset = (params.page - 1) * params.page_size
        limit = params.page_size

        if params.saved_date_start is not None and params.saved_date_end is not None:
            base_statement = select(LinkModel).where(LinkModel.saved_date.between(params.saved_date_start, params.saved_date_end))
        else:
            base_statement = select(LinkModel)

        statement = base_statement.offset(offset).limit(limit)

        try:
            links = LinkDataManager(self.session).get_links(base_statement, statement, params)
            return links
        except DatabaseError as e:
            # Handle database connection failures, downtime, etc. -> ServiceUnavailableError (503)
            self._handle_database_error(e, source=None)


    def get_link(self, id: uuid.UUID | None = None, url: str | None = None, params: RequestParameters | None = None) -> Response[LinkSchema]:
        """Get link by ID or URL."""

        try:
            if id is not None:
                link_response = LinkDataManager(self.session).get_link("id", id, params)
            elif url is not None:
                link_response = LinkDataManager(self.session).get_link("url", url, params)
            else:
                # Both id and url are missing, raise NotFoundError
                raise NotFoundError("Link not found", resource_id=None)

            if link_response.total == 0:
                # No link found for this query, raise NotFoundError
                if id is not None:
                    raise NotFoundError("Link not found", resource_id=str(id))
                else:
                    raise NotFoundError("Link not found", resource_id=url)

            return link_response
        except DatabaseConstraintError as e:
            # Use the base service method to handle constraint errors consistently
            self._handle_database_constraint_error(e, source=None)
        except DatabaseError as e:
            # Handle database connection failures, downtime, etc. -> ServiceUnavailableError (503)
            self._handle_database_error(e, source=None)


    def ingest(self, sources_list: List[str], params: IngestionParameters) -> Response[LinkSchema]:
        """Ingest links from the requested sources.

        Validate the parameters, make the calls to the third-party APIs, convert the results to schemas, 
        create the individual link, and return a response.
        """
        # ensure sources are valid
        valid_sources = {"raindrop", "tumblr", "instapaper"}
        for s in sources_list:
            if s not in valid_sources:
                raise BadRequestError(f"Invalid source: {s}. Valid sources are: {', '.join(sorted(valid_sources))}")

        # source limits from config
        source_limits = {
            "raindrop": config.raindrop.limit,
            "tumblr": config.tumblr.limit,
            "instapaper": config.instapaper.limit,
        }

        # don't let page_size exceed the smallest limit from the relevant source(s)
        min_source_limit = min(source_limits[s] for s in sources_list)
        if params.page_size is not None and params.page_size > min_source_limit:
            raise ParamValidationError(
                f"Page size value ({params.page_size}) cannot exceed {min_source_limit} because it is the smallest limit allowed for the requested sources"
            )

        # for each source in source_options, the 'limit' option should not exceed that source's limit
        if params.source_options:
            for source_name, options in params.source_options.items():
                if source_name not in valid_sources:
                    # ignore a source in source_options that isn't in the sources_list
                    pass
                if "limit" in options and options["limit"] is not None:
                    source_limit = source_limits.get(source_name)
                    if source_limit is not None and options["limit"] > source_limit:
                        raise ParamValidationError(
                            f"Limit for source {source_name} ({options['limit']}) cannot exceed the source limit ({source_limit})"
                        )

        # get an instance of the source objects and call get_links
        links = []  # list of formatted link dicts from the API objects
        for source_name in sources_list:
            if source_name == "raindrop":
                obj = Raindrop()
                obj_links = obj.get_links(params)
                links.extend(obj_links)
            elif source_name == "tumblr":
                obj = Tumblr()
                obj_links = obj.get_links(params)
                links.extend(obj_links)
            elif source_name == "instapaper":
                obj = Instapaper()
                obj_links = obj.get_links(params)
                links.extend(obj_links)

        # convert links to schemas
        schemas: List[LinkSchema] = []
        for model in links:
            schemas.append(LinkSchema(**model))

        # Create links in the database
        try:
            self.create_links(schemas)
        except DatabaseConstraintError as e:
            # Use the base service method to handle constraint errors consistently
            self._handle_database_constraint_error(e, source=sources_list)
        except DatabaseError as e:
            # Handle database connection failures, downtime, etc. -> ServiceUnavailableError (503)
            self._handle_database_error(e, source=sources_list)

        from app.schemas.response import Response
        # the return needs to match the get_links response format
        return Response.wrap(items=schemas, total=len(schemas), page=params.page, page_size=params.page_size)


class LinkDataManager(BaseDataManager):

    def add_link(self, link: LinkModel) -> None:
        """Write link to database."""

        self.add_one(link)


    def add_links(self, link_models: LinkModel) -> None:
        """Bulk write links to database."""

        self.add_all(link_models)
        #return result


    def get_links(self, base_statement, statement, params: RequestParameters | None = None) -> Response[LinkSchema]:
        """Run select statement for multiple links."""

        schemas: List[LinkSchema] = list()
        for model in self.get_all(statement):
            schemas += [LinkSchema(**model.to_dict())]

        count = self.count(base_statement)
        return Response.wrap(items=schemas, total=count, page=params.page, page_size=params.page_size)


    def get_link(self, field, value, params: RequestParameters | None = None) -> Response[LinkSchema]:
        """Run select statement for a single link."""

        statement = select(LinkModel).where(getattr(LinkModel, field) == value)
        model = self.get_one(statement)

        schemas: List[LinkSchema] = list()
        for model in self.get_all(statement):
            schemas += [LinkSchema(**model.to_dict())]

        count = self.count(statement)
        return Response.wrap(items=schemas, total=count, page=params.page, page_size=params.page_size)
