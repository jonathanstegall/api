import json
import uuid
import requests
from datetime import datetime
from app.config import config
from app.backend.ingest.link import Link

class Tumblr(Link):

    source = "tumblr"
    version = "v2"
    url: str | None = f"https://api.tumblr.com/{version}/blog/{config.tumblr.blog_id}/"

    options = Link.options
    
    options[source] = {
        "type": "link",
        "id": None,
        "tag": None,
        "limit": config.tumblr.limit,
        "offset": 0,
        "reblog_info": False,
        "notes_info": False,
        "filter": None,
        "before": False,
        "after": False,
        "sort": "desc",
        "npf": "npf"
    }


    def validate_response(self, response):
        valid_posts = []
        result = response["data"]
        if len(result) > 0:
            valid_posts = [post for post in result["response"]["posts"] if post["type"] == self.options[self.source]["type"] and post["title"] != ""]
            return valid_posts


    def get_posts(self, options = None):
        """Retrieve posts."""

        url = self.url + "posts"
        options = self.options

        type = options.get("type", None)
        id = options.get("id", None)
        tag = options.get("tag", None)
        limit = options.get("limit", config.tumblr.limit)
        offset = options.get("offset", 0)
        reblog_info = options.get("reblog_info", False)
        notes_info = options.get("notes_info", False)
        filter = options.get("filter", None)
        before = options.get("before", False)
        after = options.get("after", False)
        sort = options.get("sort", "desc")
        npf = options.get("npf", "desc")

        if type is not None:
            url = url + "/" + type + "/"
        
        url = url + "?api_key=" + config.tumblr.consumer_key

        if tag is not None:
            if isinstance(tag, str):
                url = url + "&tag=" + tag
            else:
                for key, value in tag.items():
                    url = url + "&tag[" + key + "]=" + value
        
        if limit is not None:
            url = url + "&limit=" + str(limit)

        if offset != 0:
            url = url + "&offset=" + str(offset)

        if reblog_info is not False:
            url = url + "&reblog_info=" + str(reblog_info)

        if notes_info is not False:
            url = url + "&notes_info=" + str(notes_info)

        if filter is not None:
            url = url + "&filter=" + filter

        if before is not False:
            url = url + "&before=" + before

        if after is not False:
            url = url + "&after=" + after

        if sort != "desc":
            url = url + "&sort=" + sort

        if npf != "npf":
            url = url + "&npf=" + npf

        response = requests.get(url).json()
        if response["meta"]["status"] == 200:
            return response
        else:
            raise Exception(f"Failed to fetch posts: {response["meta"]["msg"]} with status {response["meta"]["status"]}")
        

    def format_post_as_link(self, post):

        data_date = post.get("date", None)
        if data_date is not None:
            data_date = datetime.strptime(post["date"], self.date_format)
    
        data_json = ""
        try:
            data_json = json.dumps(post)
        except:
            pass
    
        creator = ""
        publisher = post.get("publisher", None)
        if publisher is not None:
            creator = post["publisher"]
    
        link = {
            "source": self.source,
            "type": post["type"],
            "id": str(uuid.uuid4()),
            "source_id": str(post["id"]),
            "date": None,
            "url": post["url"],
            "data": data_json,
            "title": post.get("title", post["url"]),
            "text": post.get("description", ""),
            "saved_date": str(data_date),
            "tags": post.get("tags", ""),
            "format": post["format"],
            "creator": creator
        }
        return link
