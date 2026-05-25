import uuid
import json
import requests
from datetime import datetime
from app.core.config import settings

# Raindrop credentials
RAINDROP_CLIENT_ID = settings.RAINDROP_CLIENT_ID
RAINDROP_CLIENT_SECRET = settings.RAINDROP_CLIENT_SECRET
RAINDROP_ACCESS_TOKEN = settings.RAINDROP_ACCESS_TOKEN
RAINDROP_LIMIT = settings.RAINDROP_LIMIT


def get_raindrop(options = None):
    """Retrieve single raindrop."""

    id = options.get("id", 0)

    # root
    url = f"https://api.raindrop.io/rest/v1/raindrop/{id}"

    # headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.RAINDROP_ACCESS_TOKEN}"
    }

    # api call
    response = requests.get(url, headers=headers).json()

    if response["result"] is True:
        return response
    else:
        raise Exception(f"Failed to fetch raindrop: {response["result"]}")

def get_raindrops(options = None):
    """Retrieve raindrops."""

    collectionId = options.get("collectionId", 0)

    # root
    url = f"https://api.raindrop.io/rest/v1/raindrops/{collectionId}"

    # headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.RAINDROP_ACCESS_TOKEN}"
    }

    search = options.get("search", "")
    sort = options.get("sort", "-created")
    page = options.get("page", None)
    perpage = options.get("perpage", settings.RAINDROP_LIMIT)
    ids = options.get("reblog_info", [])
    nested = options.get("nested", False)

    payload = {'key1': 'value1', 'key2': 'value2'}

    payload = {
        "collectionId": collectionId
    }

    if search != "":
        payload["search"] = search

    payload["sort"] = sort

    if page is not None:
        payload["page"] = page

    if perpage > settings.RAINDROP_LIMIT:
        perpage = settings.RAINDROP_LIMIT
    payload["perpage"] = perpage

    if ids:
        payload["ids"] = ids

    if nested is not False:
        payload["nested"] = True

    # api call
    response = requests.get(url, headers=headers, params=payload).json()

    if response["result"] is True:
        return response
    else:
        raise Exception(f"Failed to fetch raindrop: {response["result"]}")
    

def format_raindrop_as_link(raindrop):

    format = "%Y-%m-%dT%H:%M:%S.%fZ"
    
    raindrop_date = None
    if raindrop["created"]:
        raindrop_date = datetime.strptime(raindrop["created"], format)

    raindrop_data = ""
    try:
        raindrop_data = json.dumps(raindrop)
    except:
        pass

    raindrop = {
        "source": "raindrop",
        "type": raindrop["type"],
        "id": uuid.uuid4(),
        "source_id": str(raindrop["_id"]),
        "date": None,
        "url": raindrop["link"],
        "data": raindrop_data,
        "title": raindrop.get("title", raindrop["link"]),
        "text": raindrop.get("excerpt", ""),
        "saved_date": raindrop_date,
        "tags": raindrop["tags"]
    }
    return raindrop
