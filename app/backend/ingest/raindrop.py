import json
import uuid
import requests
from datetime import datetime
from app.config import config
from app.backend.ingest.link import Link

class Raindrop(Link):

    source = "raindrop"
    date_format = "%Y-%m-%dT%H:%M:%S.%fZ"
    version = "v1"
    url: str | None = f"https://api.raindrop.io/rest/{version}/"

    # Raindrop credentials
    RAINDROP_CLIENT_ID = config.raindrop.client_id
    RAINDROP_CLIENT_SECRET = config.raindrop.client_secret

    options = Link.options
    
    options[source] = {
        "id": 0,
        "collectionId": 0,
        "search": "",
        "sort": "-created",
        "page": None,
        "perpage": config.raindrop.limit,
        "ids": [],
        "nested": False
    }


    def get_posts(self, options = None):
        options = self.options
        raindrops = []
        # fetch raindrops
        if self.options["raindrop"]["id"] > 0:
            raindrops = self.get_raindrop(
                options = options[self.source]
            )
        else:
            raindrops = self.get_raindrops(
                options = options[self.source]
            )
        return raindrops


    def validate_response(self, response):
        #response = response["data"]
        if "item" in response["data"]:
            valid_raindrops.append(response["data"]["item"])
        if "items" in response["data"]:
            valid_raindrops = [raindrop_item for raindrop_item in response["data"]["items"] if raindrop_item["title"] != ""]
        return valid_raindrops


    def get_raindrop(self, options = None):
        """Retrieve single raindrop."""

        id = self.options.get("id", 0)

        # root
        url = f"{self.url}raindrop/{id}"

        # headers
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.raindrop.access_token}"
        }

        # api call
        response = requests.get(url, headers=headers).json()

        if response["result"] is True:
            return response
        else:
            raise Exception(f"Failed to fetch raindrop: {response["result"]}")


    def get_raindrops(self, options = None):
        """Retrieve raindrops."""

        collectionId = options.get("collectionId", 0)

        # root
        url = f"{self.url}raindrops/{collectionId}"

        # headers
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.raindrop.access_token}"
        }

        search = options.get("search", "")
        sort = options.get("sort", "-created")
        page = options.get("page", None)
        perpage = options.get("perpage", config.raindrop.limit)
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

        if perpage > config.raindrop.limit:
            perpage = config.raindrop.limit
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
        

    def format_post_as_link(self, raindrop):
        
        raindrop_date = None
        if raindrop["created"]:
            raindrop_date = datetime.strptime(raindrop["created"], self.date_format)

        raindrop_data = ""
        try:
            raindrop_data = json.dumps(raindrop)
        except:
            pass

        raindrop = {
            "source": "raindrop",
            "type": raindrop["type"],
            "id": str(uuid.uuid4()),
            "source_id": str(raindrop["_id"]),
            "date": None,
            "url": raindrop["link"],
            "data": raindrop_data,
            "title": raindrop.get("title", raindrop["link"]),
            "text": raindrop.get("excerpt", ""),
            "saved_date": str(raindrop_date),
            "tags": raindrop["tags"]
        }
        return raindrop
