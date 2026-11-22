import json
import uuid
import requests
from datetime import datetime
from app.config import config
from app.backend.ingest.link import Link

class Instapaper(Link):

    source = "instapaper"
    version = "2"
    url: str | None = f"https://www.instapaper.com/api/"
    date_format = "%Y-%m-%d"

    options = Link.options
    
    options[source] = {
        "type": "bookmark",
        "section": "home",
        "folder_id": None,
        "folder_name": None,
        "tag": None,
        "limit": config.instapaper.limit,
        "page": None,
        "page_size": None,
        "offset": 0,
        "since": None
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


    def _apply_ingest_params(self, params):
        """Apply ingestion parameters to the source-specific options."""
        if self.source is None or self.source not in self.options:
            return
        base_opt = self.options[self.source]
        # Get source-specific options from URL params (if any)
        source_opts = params.source_options.get(self.source) if params.source_options else None
        if source_opts is not None:
            # Copy base_opt to avoid mutating the shared class dict
            opt = base_opt.copy()
            # Update opt with source-specific keys from source_opts
            for k, v in source_opts.items():
                opt[k] = v
        else:
            opt = base_opt
        
        # Tag
        tag = source_opts.get('tag') if source_opts is not None else None
        if tag is not None:
            opt["tag"] = tag
        
        # Folder
        folder_name = source_opts.get('folder_name') if source_opts is not None else None
        if folder_name is not None:
            # Get the numeric ID of the folder
            folder_id = self.get_folder_id(folder_name)
            if not folder_id:
                raise Exception(f"No such folder named {folder_name}")
            opt["folder_id"] = folder_id

        # Date filtering
        since = source_opts.get('since') if source_opts is not None else None
        if since is not None:
            try:
                dt = datetime.strptime(since, self.date_format)
                opt["since"] = dt.timestamp()
            except Exception:
                pass
        
        # Pagination
        page = source_opts.get('page') if source_opts is not None else None
        page_size = source_opts.get('page_size') if source_opts is not None else None
        if page is not None and page_size is not None:
            opt["offset"] = (page - 1) * page_size
            opt["limit"] = page_size

        offset = source_opts.get('offset') if source_opts is not None else None
        limit = source_opts.get('limit') if source_opts is not None else None
        if offset is not None and limit is not None:
            opt["offset"] = offset
            opt["limit"] = limit


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
        
        params = {}

        section = options.get("section", "home")
        folder_name = options.get("folder_name", None)
        tag = options.get("tag", None)
        limit = options.get("limit", config.instapaper.limit)
        offset = options.get("offset", 0)
        since = options.get("since", None)

        if section is None and tag is not None:
            section = "tag"

        if section is None and folder_name is not None:
            section = "folder"

        if since is not None:
            section = None

        if folder_name is not None and tag is not None:
            raise Exception(f"A request cannot have both a folder and a tag. This request has folder {folder_name} and tag {tag}")

        if section is not None:
            params["section"] = section

        if folder_name is not None:
            # Get the numerical ID of the folder
            folder_id = self.get_folder_id(folder_name)
            if not folder_id:
                raise Exception(f"No such folder named {folder_name}")
            params["folder_id"] = folder_id

        if tag is not None:
            params["tag"] = tag

        if limit is not None:
            params["limit"] = limit

        if offset is not None:
            params["offset"] = offset

        if since is not None:
            dt = datetime.strptime(since, self.date_format)
            params["since"] = dt.timestamp()        

        # Fetch bookmarks
        url = f"{self.url}{self.version}/bookmarks"

        # api call
        response = requests.get(url, headers=self.headers, params=params).json()
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
            "date": bookmark["pubtime"],
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
