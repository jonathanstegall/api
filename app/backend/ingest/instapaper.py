import json
import uuid
import requests
from app.config import config
from app.backend.ingest.link import Link

class Instapaper(Link):

    source = "instapaper"
    version = "2"
    url: str | None = f"https://www.instapaper.com/api/"

    options = Link.options
    
    options[source] = {
        "type": "bookmark",
        "have": [],
        "folder_id": "unread"
    }

    # headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.instapaper.access_token}"
    }

    def get_posts(self, options = None):
        options = self.options

        # fetch Instapaper bookmarks
        posts = self.get_bookmarks(
            options = options[self.source]
        )
        return posts


    def validate_response(self, response):
        valid_posts = [bookmark for bookmark in response["bookmarks"] if bookmark["title"] != ""]
        return valid_posts


    def get_folder_id(self, folder_name):
        """Retrieve the numerical ID of a folder given its name."""
        url = f"{self.url}{self.version}/folders/"
        response = requests.get(url, headers=self.headers).json()
        if response.status_code == 200:
            folders = response.json()
            for folder in folders:
                if folder.get("type") == "folder" and folder.get("title") == folder_name:
                    return folder.get("folder_id")
            return None
        else:
            raise Exception(f"Failed to fetch folders: {response.text}")


    def get_bookmarks(self, options = None):
        """Retrieve bookmarks, optionally from a specific Instapaper folder by its name."""
        
        request_data = {}

        limit = options.get("limit", config.instapaper.limit)
        tag = options.get("tag", None)
        folder_name = options.get("folder_name", None)
        highlights = options.get("highlights", None)
        have = options.get("have", None)

        if limit is not None:
            request_data["limit"] = limit

        if folder_name is not None:
            # Get the numerical ID of the folder
            folder_id = self.get_folder_id(folder_name)
            if not folder_id:
                raise Exception(f"No such folder named {folder_name}")
            request_data["folder_id"] = folder_id

        if folder_name is None and tag is not None:
            request_data["tag"] = tag

        if have is not None:
            if isinstance(have, str):
                have = [have]
            request_data["have"] = ','.join(have)
        
        if highlights is not None:
            request_data["highlights"] = highlights

        # Fetch bookmarks
        url = f"{self.url}{self.version}/bookmarks"

        # api call
        response = requests.get(url, headers=self.headers).json()
        # TODO: handle paging more than 500 bookmarks
        if response["total"] > 0:
            return response
        else:
            raise Exception(f"Failed to fetch bookmarks: {response}")
        

    def format_post_as_link(self, bookmark):
        bookmark = {
            "source": self.source,
            "type": "bookmark",
            "id": str(uuid.uuid4()),
            "source_id": str(bookmark["id"]),
            "date": None,
            "url": bookmark["url"],
            "data": json.dumps(bookmark),
            "title": bookmark.get("title", bookmark["url"]),
            "text": bookmark.get("description", ""),
            "saved_date": bookmark["time"]
        }
        return bookmark


    def create_folder(self, folder_name):
        """Create a new Instapaper folder."""
        url = f"{self.url}{self.version}/folders"
        response = requests.post(url, headers=self.headers, data={"title": folder_name})
        if response.status_code == 200:
            return response.json()[0]["folder_id"]
        else:
            raise Exception(f"Failed to create folder: {response.text}")
        

    def list_folders(self):
        """List all Instapaper folders."""

        # response is like this
        # [{'type': 'folder', 'folder_id': 5367019, 'title': 'test folder', 'display_title': 'test folder', 'slug': 'test-folder', 'sync_to_mobile': 1, 'position': 1779640105, 'public': 0, 'count': 1}]

        url = f"{self.url}{self.version}/folders"
        response = requests.get(url, headers=self.headers).json()
        if "folders" in response:
            response_data = response.json()
            return response_data
        else:
            raise Exception(f"Failed to fetch folders: {response.text}")
        

    def move_bookmark(self, bookmark_id, folder_id):
        """Move a bookmark to an Instapaper folder."""
        api_url = f"{self.url}{self.version}/bookmarks/{bookmark_id}/move"
        data = {
            "section": folder_id
        }
        response = requests.post(api_url, headers=self.headers, data=data)
        if response.status_code != 200:
            raise Exception(f"Failed to move bookmark: {response.text}")


    def save_bookmark(self, folder_id, url, title, description):
        """Save a bookmark to Instapaper."""
        api_url = f"{self.url}{self.version}/bookmarks"
        data = {
            "url": url,
            "title": title,
            "description": description,
            "folder_id": folder_id,
        }
        response = requests.post(api_url, headers=self.headers, data=data)
        if response.status_code != 200:
            raise Exception(f"Failed to save bookmark: {response.text}")


    def generate_unique_folder_name(self, base_name):
        """Generate a unique folder name based on the base name."""
        unique_suffix = str(uuid.uuid4())[:4]  # Generate a short unique identifier
        return f"{base_name}-{unique_suffix}"
