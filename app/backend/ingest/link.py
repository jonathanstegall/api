import json
from datetime import datetime

from app.config import config

from app.backend.cache.cache import get_json, set_json, cache_key_builder

class Link:

    date_format: str | None = "%Y-%m-%d %H:%M:%S %Z"
    source: str | None = None
    url: str | None = None

    options = {
        "cache_data": config.cache.use_cache,
        "cache_ttl" : config.cache.ttl,
        "overwrite_cache": config.cache.overwrite_cache,
        "skip_cache": config.cache.skip_cache,
        "skip_existing_links": True
    }

    def __init__(self):
        self.source = self.__class__.source

    def get_links(self, params=None):
        """Get links from the source. Applies ingestion params and retrieves data."""
        if params is not None:
            self._apply_ingest_params(params)
        response = self.retrieve_data()
        valid_posts = self.validate_response(response)

        # format bookmarks as links
        format_links = [self.format_post_as_link(post) for post in valid_posts]
        return format_links


    def retrieve_data(self):
        """Retrieve posts, checking cache first."""
        cached_posts = self.check_cache(self.options, self.source)
        if cached_posts is not None:
            return cached_posts
        posts_response = self.get_posts()
        posts_cached = self.save_to_cache(self.options, self.source, posts_response)
        return posts_cached
    
    
    def validate_response(self, response):
        """Extract list of posts from response. Base implementation returns 'data' field if it's a list."""
        if isinstance(response, dict) and "data" in response:
            data = response["data"]
            if isinstance(data, list):
                return data
        return []


    def format_post_as_link(self, post):
        """Format a post dict into a link dict. Base implementation uses minimal fields."""
        return {
            "source": self.source,
            "id": str(id(post)),
            "url": post.get("url", ""),
            "title": post.get("title", ""),
            "text": post.get("text", ""),
            "date": None
        }


    def get_posts(self):
        """Fetch posts from the external source. Must be overridden by subclasses."""
        raise NotImplementedError("get_posts must be implemented by subclasses")


    def _apply_ingest_params(self, params):
        """Apply ingestion parameters to the source-specific options."""
        if self.source is None or self.source not in self.options:
            return
        base_opt = self.options[self.source]
        source_opts = params.source_options.get(self.source) if params.source_options else None
        if source_opts is not None:
            # Copy base_opt to avoid mutating the shared class dict
            opt = base_opt.copy()
            for k, v in source_opts.items():
                opt[k] = v
        else:
            opt = base_opt
        # subclasses override to set their specific fields from `opt`



    def check_cache(self, options, source):
        response = None

        friendly_cache_key = "posts:"
        for key, value in options[source].items():
            friendly_cache_key += f"{key}:{value},"
        cache_key = cache_key_builder(self, key=friendly_cache_key)

        # Check cache
        cached_response = get_json(cache_key)
        if cached_response is not None and options["skip_cache"] is False:
            response = cached_response
            if isinstance(response, dict) and "data" in response:
                response = response["data"]
            response["cache_status"] = "existing"
        return response

    
    def save_to_cache(self, options, source, posts):
        """Save posts to cache if cache is enabled."""
        friendly_cache_key = "posts:"
        for key, value in options[source].items():
            friendly_cache_key += f"{key}:{value},"
        cache_key = cache_key_builder(self, key=friendly_cache_key)

        # Save to cache
        if posts is not None and (options["cache_data"] is True or options["overwrite_cache"] is True):
            cache_data = {
                "data": posts,
                "cache_status": "new",
                "generated": str(datetime.now())
            }
            set_json(cache_key, cache_data)
        return posts
