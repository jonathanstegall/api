import uuid
import json
import requests
from datetime import datetime
from app.core.config import settings

# Tumblr credentials
TUMBLR_CONSUMER_KEY = settings.TUMBLR_CONSUMER_KEY
TUMBLR_CONSUMER_SECRET = settings.TUMBLR_CONSUMER_SECRET
TUMBLR_BLOG_ID = settings.TUMBLR_BLOG_ID
TUMBLR_LIMIT = settings.TUMBLR_LIMIT


def get_tumblr_posts(options = None):
    """Retrieve posts."""

    # root
    url = f"https://api.tumblr.com/v2/blog/{TUMBLR_BLOG_ID}/posts"

    type = options.get("type", None)
    id = options.get("id", None)
    tag = options.get("tag", None)
    limit = options.get("limit", settings.TUMBLR_LIMIT)
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
    
    url = url + "?api_key=" + TUMBLR_CONSUMER_KEY

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
    

def format_post_as_link(post):

    format = '%Y-%m-%d %H:%M:%S %Z'
    
    post_date = None
    if post["date"]:
        post_date = datetime.strptime(post["date"], format)

    post_data = ""
    try:
        post_data = json.dumps(post)
    except:
        pass

    creator = ""
    publisher = post.get("publisher", None)
    if publisher is not None:
        creator = post["publisher"]

    post = {
        "source": "tumblr",
        "type": post["type"],
        "id": uuid.uuid4(),
        "source_id": str(post["id"]),
        "date": None,
        "url": post["url"],
        "data": post_data,
        "title": post.get("title", post["url"]),
        "text": post.get("description", ""),
        "saved_date": post_date,
        "tags": post["tags"],
        "format": post["format"],
        "creator": creator
    }
    return post
