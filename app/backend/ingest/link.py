import json
from datetime import datetime

from fastapi import FastAPI, HTTPException

from app.config import config

from app.backend.cache.cache import get_json, set_json, cache_key_builder

class Link():

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

        super()


    def get_links(self):
        response = self.retrieve_data()
        valid_posts = self.validate_response(response)

        # format bookmarks as links
        format_links = [self.format_post_as_link(post) for post in valid_posts]
        #links = format_links
        if "generated" in response and "cache_status" in response:
            headers = {"X-Cache-Generated": response["generated"]}
            if response["cache_status"] == "existing":
                headers["X-Cache"] = "HIT"
            else:
                headers["X-Cache"] = "SAVED"

        #links = {
        #    "content": format_links,
        #    "headers": headers
        #}

        return format_links


    def retrieve_data(self):
        posts = []

        cached_posts = self.check_cache(self.options, self.source)
        if cached_posts is not None:
            return cached_posts

        # fetch external posts
        posts = self.get_posts(
            options = self.options[self.source]
        )
        posts = self.save_to_cache(self.options, self.source, posts)
        return posts


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
            response["cache_status"] = "existing"
        return response

    
    def save_to_cache(self, options, source, posts):
        friendly_cache_key = "posts:"
        for key, value in options[source].items():
            friendly_cache_key += f"{key}:{value},"
        cache_key = cache_key_builder(self, key=friendly_cache_key)

        response = posts
        if response is not None and (options["cache_data"] is True or options["overwrite_cache"] is True):
            cache_data = {
                "data": posts,
                "cache_status": "new",
                "generated": json.dumps(datetime.now(), default=str),
            }
            save_to_cache = set_json(cache_key, cache_data)
            if save_to_cache["data"] is not None:
                response = save_to_cache
        return response

