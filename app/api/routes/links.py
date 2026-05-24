import uuid
import datetime as dt
from typing import Any

from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import col, func, select

from app.dependencies import get_cache
from app.services.cache import CacheService

from app.api.deps import SessionDep
from app.models import Link, LinkCreate, LinkPublic, LinksPublic, LinkUpdate, Message

from app.external import instapaper

from app.core.config import settings

router = APIRouter(prefix="/links", tags=["links"])


@router.get("/", response_model=LinksPublic)
def read_links(
    session: SessionDep, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve links.
    """

    count_statement = select(func.count()).select_from(Link)
    count = session.exec(count_statement).one()
    statement = (
        select(Link).order_by(col(Link.created_at).desc()).offset(skip).limit(limit)
    )
    links = session.exec(statement).all()

    links_public = [LinkPublic.model_validate(link) for link in links]
    return LinksPublic(data=links_public, count=count)


@router.get("/scan", response_model=LinksPublic)
async def scan_for_links(session: SessionDep, cache: CacheService = Depends(get_cache), source: str | None = None) -> Any:
    """
    Get links.
    """

    options = {
        "cache_data": settings.CACHE_DATA,
        "cache_ttl" : settings.REDIS_TTL,
        "overwrite_cache": settings.OVERWRITE_CACHE,
        "bypass_cache": False,
        "skip_existing_links": False,
        "have": [],
        "folder_id": "unread"
    }

    sources = source.split(",")
    links_public = []
    
    if options["skip_existing_links"] is True:
        for source in sources:
            existing_links = session.query(Link.source_id).filter(Link.source == source).all()
            if existing_links and source == "instapaper":
                for link in existing_links:
                    options["have"].append(link[0])

    if "instapaper" in sources:
        # Step 1: Get Instapaper OAuth tokens
        oauth_token, oauth_token_secret = instapaper.get_instapaper_access_token()
        instapaper_session = instapaper.authenticate_instapaper(oauth_token, oauth_token_secret)

        # Step 2: Fetch Instapaper bookmarks
        async def fetch_bookmarks():
            bookmarks = instapaper.get_instapaper_bookmarks(
                session = instapaper_session,
                options = options
            )
            return bookmarks

        cache_key = f"bookmarks:{options["folder_id"]}"
        bookmarks = await cache.remember(cache_key, fetch_bookmarks, options)
        valid_bookmarks = [bookmark for bookmark in bookmarks["result"] if bookmark["type"] == "bookmark" and bookmark["title"] != ""]

        folders = instapaper.list_instapaper_folders(session=instapaper_session)
        print(folders)

        # Step 3: format bookmarks as links
        format_links = [instapaper.format_bookmark_as_link(bookmark) for bookmark in valid_bookmarks]
        links = format_links
        links_instapaper = [Link.model_validate(link) for link in links]
        links_public.extend(links_instapaper)

    # Step 4: add metadata
    meta = {
        "sources": source,
        "count": len(links),
        "cache_key": cache_key,
        "from_cache": bookmarks["from_cache"],
        "cache_generated": bookmarks.get("cache_generated", None),
        "cache_ttl": bookmarks["cache_ttl"],
        "cache_expiration": bookmarks.get("cache_expiration", None)
    }

    return LinksPublic(data=links_public, meta = meta)


@router.get("/{id}", response_model=LinkPublic)
def read_link(session: SessionDep, id: uuid.UUID) -> Any:
    """
    Get link by ID.
    """
    link = session.get(Link, id)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    return link


@router.post("/", response_model=LinkPublic)
def create_link(
    *, session: SessionDep, link_in: LinkCreate
) -> Any:
    """
    Create new link.
    """
    link = Link.model_validate(link_in)
    session.add(link)
    session.commit()
    session.refresh(link)
    return link


@router.put("/{id}", response_model=LinkPublic)
def update_link(
    *,
    session: SessionDep,
    id: uuid.UUID,
    link_in: LinkUpdate,
) -> Any:
    """
    Update a link.
    """
    link = session.get(Link, id)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    update_dict = link_in.model_dump(exclude_unset=True)
    link.sqlmodel_update(update_dict)
    session.add(link)
    session.commit()
    session.refresh(link)
    return link


@router.delete("/{id}")
def delete_link(
    session: SessionDep, id: uuid.UUID
) -> Message:
    """
    Delete a link.
    """
    link = session.get(Link, id)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    session.delete(link)
    session.commit()
    return Message(message="Link deleted successfully")
