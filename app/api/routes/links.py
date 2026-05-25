import uuid
import datetime as dt
from typing import Any

from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import col, func, select

from app import crud

from app.dependencies import get_cache
from app.services.cache import CacheService

from app.api.deps import SessionDep
from app.models import Link, LinkCreate, LinkPublic, LinksPublic, LinkUpdate, Message

from app.external import instapaper, tumblr

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
        "skip_existing_links": True,
        "instapaper": {
            "have": [],
            "folder_id": "unread"
        },
        "tumblr": {
            "type": "link",
            "id": None,
            "tag": None,
            "limit": settings.TUMBLR_LIMIT,
            "offset": 0,
            "reblog_info": False,
            "notes_info": False,
            "filter": None,
            "before": False,
            "after": False,
            "sort": "desc",
            "npf": "npf"
        }
    }

    sources = source.split(",")
    friendly_cache_key = ""
    links_public = []
    from_cache = False
    cache_generated = None
    cache_ttl = None
    cache_expiration = None
    
    # skip existing links
    if options["skip_existing_links"] is True:
        for source in sources:
            existing_links = session.query(Link.source_id).filter(Link.source == source).all()
            if existing_links and source == "instapaper":
                for link in existing_links:
                    options["instapaper"]["have"].append(link[0])
            if existing_links and source == "tumblr":
                options["tumblr"]["offset"] = len(existing_links)

    if "instapaper" in sources:
        # authenticate Instapaper
        oauth_token, oauth_token_secret = instapaper.get_instapaper_access_token()
        instapaper_session = instapaper.authenticate_instapaper(oauth_token, oauth_token_secret)

        # fetch Instapaper bookmarks
        async def fetch_bookmarks():
            bookmarks = instapaper.get_instapaper_bookmarks(
                session = instapaper_session,
                options = options["instapaper"]
            )
            return bookmarks

        cache_key = f"bookmarks:{options["instapaper"]["folder_id"]}"
        friendly_cache_key = cache_key
        bookmarks = await cache.remember(cache_key, fetch_bookmarks, options)
        if bookmarks["from_cache"] is True:
            from_cache = True
            cache_ttl = cache_ttl
            cache_generated = bookmarks.get("cache_generated", None)
        valid_bookmarks = [bookmark for bookmark in bookmarks["result"] if bookmark["type"] == "bookmark" and bookmark["title"] != ""]

        # format bookmarks as links
        format_links = [instapaper.format_bookmark_as_link(bookmark) for bookmark in valid_bookmarks]
        links = format_links
        links_instapaper = [Link.model_validate(link) for link in links]
        links_public.extend(links_instapaper)

    if "tumblr" in sources:

        valid_posts = []

        # fetch Tumblr posts
        async def fetch_posts():
            posts = tumblr.get_tumblr_posts(
                options = options["tumblr"]
            )
            return posts

        friendly_cache_key = "posts:"
        for key, value in options["tumblr"].items():
            friendly_cache_key += f"{key}:{value},"
        cache_key = cache.hash_key(friendly_cache_key)
        posts = await cache.remember(cache_key, fetch_posts, options)
        if posts["from_cache"] is True:
            from_cache = True
            cache_generated = posts.get("cache_generated", None)
            cache_ttl = posts.get("cache_ttl", None)
            cache_expiration = posts.get("cache_expiration", None)
        if len(posts["result"]) > 0:
            valid_posts = [post for post in posts["result"]["response"]["posts"] if post["type"] == options["tumblr"]["type"] and post["title"] != ""]

        # format bookmarks as links
        format_links = [tumblr.format_post_as_link(post) for post in valid_posts]
        links = format_links
        links_tumblr = [Link.model_validate(link) for link in links]
        links_public.extend(links_tumblr)

    # add metadata
    meta = {
        "sources": source,
        "count": len(links),
        "cache_key": friendly_cache_key,
        "from_cache": from_cache,
        "cache_generated": cache_generated,
        "cache_ttl": cache_ttl,
        "cache_expiration": cache_expiration
    }

    return LinksPublic(data=links_public, meta = meta)


@router.get("/save", response_model=LinksPublic)
async def save(session: SessionDep, cache: CacheService = Depends(get_cache), source: str | None = None) -> Any:
    """
    Save links.
    """

    options = {
        "check_cache": True,
        "check_source": True,
        "skip_existing_urls": True,
        "update_existing_urls": False,
        "empty_cache": True,
        "instapaper": {
            "folder_id": "unread"
        },
        "tumblr": {
            "type": "link",
            "id": None,
            "tag": None,
            "limit": settings.TUMBLR_LIMIT,
            "offset": 0,
            "reblog_info": False,
            "notes_info": False,
            "filter": None,
            "before": False,
            "after": False,
            "sort": "desc",
            "npf": "npf"
        }
    }

    bookmarks = []
    sources = source.split(",")
    links_public = []
    friendly_cache_key = ""

    # empty callback
    def fetch_links():
        return []

    meta = {}

    if "instapaper" in sources:
        cache_key = f"bookmarks:{options["instapaper"]["folder_id"]}"
        friendly_cache_key = cache_key
    
        if options["check_cache"] is True:
            bookmarks = await cache.remember(cache_key, fetch_links, options)
            valid_bookmarks = [bookmark for bookmark in bookmarks["result"] if bookmark["type"] == "bookmark" and bookmark["title"] != ""]
            if len(valid_bookmarks) > 0:
                meta["from_cache"] = True

        if options["check_source"] is True:
            bookmarks = await scan_for_links(session, cache, "instapaper")
            format_links = [instapaper.format_bookmark_as_link(bookmark) for bookmark in valid_bookmarks]
            source_bookmarks = []
            for item in format_links:
                if item not in valid_bookmarks:
                    source_bookmarks.append(item)

        # format bookmarks as links
        format_links = [instapaper.format_bookmark_as_link(bookmark) for bookmark in valid_bookmarks]
        links = []
        for link in format_links:
            try:
                links.append(crud.create_link(session=session, link_create=link))
            except:
                pass
        # merge with overall links
        links_public.extend(links)

    if "tumblr" in sources:

        # match offset
        existing_links = session.query(Link.source_id).filter(Link.source == "tumblr").all()
        if existing_links:
            options["tumblr"]["offset"] = len(existing_links)

        valid_posts = []
        friendly_cache_key = "posts:"
        for key, value in options["tumblr"].items():
            friendly_cache_key += f"{key}:{value},"
        cache_key = cache.hash_key(friendly_cache_key)

        if options["check_cache"] is True:
            posts = await cache.remember(cache_key, fetch_links, options)
            if len(posts["result"]) > 0:
                valid_posts = [post for post in posts["result"]["response"]["posts"] if post["type"] == options["tumblr"]["type"] and post["title"] != ""]
                if len(valid_posts) > 0:
                    meta["from_cache"] = True

        if options["check_source"] is True:
            posts = await scan_for_links(session, cache, "tumblr")
            format_links = [tumblr.format_post_as_link(post) for post in valid_posts]
            source_posts = []
            for item in format_links:
                if item not in valid_posts:
                    source_posts.append(item)

        valid_posts.extend(source_posts)

        # format posts as links
        format_links = [tumblr.format_post_as_link(post) for post in valid_posts]
        links = []
        for link in format_links:
            try:
                links.append(crud.create_link(session=session, link_create=link))
            except:
                #raise ValueError("something brke")
                pass
        # merge with overall links
        links_public.extend(links)

    meta["count"] = len(links_public)
    if friendly_cache_key:
        meta["cache_key"] = friendly_cache_key
    if options["empty_cache"] is True:
        await cache.delete(cache_key)

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
