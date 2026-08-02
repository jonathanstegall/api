import json
import uuid
from requests_oauthlib import OAuth1Session
from app.config import config
from app.backend.ingest.link import Link

class Instapaper(Link):

    source = "instapaper"
    url: str | None = f"https://www.instapaper.com/api/"

    options = Link.options
    
    options[source] = {
        "type": "bookmark",
        "have": [],
        "folder_id": "unread"
    }

    def get_posts(self, options = None):
        options = self.options
        # authenticate Instapaper
        oauth_token, oauth_token_secret = self.get_access_token()
        instapaper_session = self.authenticate(oauth_token, oauth_token_secret)

        # fetch Instapaper bookmarks
        posts = self.get_bookmarks(
            session = instapaper_session,
            options = options["instapaper"]
        )
        return posts


    def validate_response(self, response):
        valid_posts = [bookmark for bookmark in response["data"] if bookmark["type"] == "bookmark" and bookmark["title"] != ""]
        return valid_posts


    def get_access_token(self):
        """Obtain OAuth access token using xAuth."""
        url = f"{self.url}1/oauth/access_token"
        oauth = OAuth1Session(
            config.instapaper.consumer_key, client_secret=config.instapaper.consumer_secret
        )
        data = {
            "x_auth_username": config.instapaper.username,
            "x_auth_password": config.instapaper.password,
            "x_auth_mode": "client_auth",
        }
        response = oauth.post(url, data=data)
        if response.status_code == 200:
            token_data = dict(item.split("=") for item in response.text.split("&"))
            return token_data["oauth_token"], token_data["oauth_token_secret"]
        else:
            raise Exception(f"Failed to get access token: {response.text}")


    def authenticate(self, oauth_token, oauth_token_secret):
        """Authenticate with Instapaper using OAuth."""
        return OAuth1Session(
            config.instapaper.consumer_key,
            client_secret=config.instapaper.consumer_secret,
            resource_owner_key=oauth_token,
            resource_owner_secret=oauth_token_secret,
        )


    def get_folder_id(self, session, folder_name):
        """Retrieve the numerical ID of a folder given its name."""
        url = f"{self.url}1.1/folders/list"
        response = session.post(url)
        if response.status_code == 200:
            folders = response.json()
            for folder in folders:
                if folder.get("type") == "folder" and folder.get("title") == folder_name:
                    return folder.get("folder_id")
            return None
        else:
            raise Exception(f"Failed to fetch folders: {response.text}")


    def get_bookmarks(self, session, options = None):
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
            folder_id = self.get_folder_id(session, folder_name)
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
        url = f"{self.url}1/bookmarks/list"

        response = session.post(url, data=request_data)
        # TODO: handle paging more than 500 bookmarks
        if response.status_code == 200:
            response_data = response.json()
            return response_data
        else:
            raise Exception(f"Failed to fetch bookmarks: {response.text}")
        

    def format_post_as_link(self, bookmark):
        bookmark = {
            "source": self.source,
            "type": "bookmark",
            "id": str(uuid.uuid4()),
            "source_id": str(bookmark["bookmark_id"]),
            "date": None,
            "url": bookmark["url"],
            "data": json.dumps(bookmark),
            "title": bookmark.get("title", bookmark["url"]),
            "text": bookmark.get("description", ""),
            "saved_date": bookmark["time"],
            "hash": bookmark["hash"]
        }
        return bookmark


    def create_folder(self, session, folder_name):
        """Create a new Instapaper folder."""
        url = f"{self.url}1/folders/add"
        response = session.post(url, data={"title": folder_name})
        if response.status_code == 200:
            return response.json()[0]["folder_id"]
        else:
            raise Exception(f"Failed to create folder: {response.text}")
        

    def list_folders(self, session):
        """List all Instapaper folders."""

        # response is like this
        # [{'type': 'folder', 'folder_id': 5367019, 'title': 'test folder', 'display_title': 'test folder', 'slug': 'test-folder', 'sync_to_mobile': 1, 'position': 1779640105, 'public': 0, 'count': 1}]

        url = f"{self.url}1/folders/list"
        response = session.post(url)
        if response.status_code == 200:
            response_data = response.json()
            return response_data
        else:
            raise Exception(f"Failed to fetch folders: {response.text}")
        

    def move_bookmark(self, session, bookmark_id, folder_id):
        """Move a bookmark to an Instapaper folder."""
        api_url = f"{self.url}1/bookmarks/move"
        data = {
            "bookmark_id": bookmark_id,
            "folder_id": folder_id
        }
        response = session.post(api_url, data=data)
        if response.status_code != 200:
            raise Exception(f"Failed to move bookmark: {response.text}")


    def save_bookmark(self, session, folder_id, url, title, description):
        """Save a bookmark to Instapaper."""
        api_url = f"{self.url}1/bookmarks/add"
        data = {
            "url": url,
            "title": title,
            "description": description,
            "content": description,
            "folder_id": folder_id,
        }
        response = session.post(api_url, data=data)
        if response.status_code != 200:
            raise Exception(f"Failed to save bookmark: {response.text}")


    def generate_unique_folder_name(self, base_name):
        """Generate a unique folder name based on the base name."""
        unique_suffix = str(uuid.uuid4())[:4]  # Generate a short unique identifier
        return f"{base_name}-{unique_suffix}"
