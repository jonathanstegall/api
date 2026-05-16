import uuid
from requests_oauthlib import OAuth1Session
from app.core.config import settings

# Instapaper credentials
INSTAPAPER_CONSUMER_KEY = settings.INSTAPAPER_CONSUMER_KEY
INSTAPAPER_CONSUMER_SECRET = settings.INSTAPAPER_CONSUMER_SECRET
INSTAPAPER_USERNAME = settings.INSTAPAPER_USERNAME
INSTAPAPER_PASSWORD = settings.INSTAPAPER_PASSWORD


def get_instapaper_access_token():
    """Obtain OAuth access token using xAuth."""
    url = "https://www.instapaper.com/api/1/oauth/access_token"
    oauth = OAuth1Session(
        INSTAPAPER_CONSUMER_KEY, client_secret=INSTAPAPER_CONSUMER_SECRET
    )
    data = {
        "x_auth_username": INSTAPAPER_USERNAME,
        "x_auth_password": INSTAPAPER_PASSWORD,
        "x_auth_mode": "client_auth",
    }
    response = oauth.post(url, data=data)
    if response.status_code == 200:
        token_data = dict(item.split("=") for item in response.text.split("&"))
        return token_data["oauth_token"], token_data["oauth_token_secret"]
    else:
        raise Exception(f"Failed to get access token: {response.text}")


def authenticate_instapaper(oauth_token, oauth_token_secret):
    """Authenticate with Instapaper using OAuth."""
    return OAuth1Session(
        INSTAPAPER_CONSUMER_KEY,
        client_secret=INSTAPAPER_CONSUMER_SECRET,
        resource_owner_key=oauth_token,
        resource_owner_secret=oauth_token_secret,
    )


def get_instapaper_folder_id(session, folder_name):
    """Retrieve the numerical ID of a folder given its name."""
    url = "https://www.instapaper.com/api/1.1/folders/list"
    response = session.post(url)
    if response.status_code == 200:
        folders = response.json()
        for folder in folders:
            if folder.get("type") == "folder" and folder.get("title") == folder_name:
                return folder.get("folder_id")
        return None
    else:
        raise Exception(f"Failed to fetch folders: {response.text}")


def get_instapaper_bookmarks(session, folder_name = None):
    """Retrieve bookmarks, optionally from a specific Instapaper folder by its name."""
    
    if folder_name is not None:
        # Get the numerical ID of the folder
        folder_id = get_instapaper_folder_id(session, folder_name)
        if not folder_id:
            raise Exception(f"No such folder named {folder_name}")

    # Fetch bookmarks
    url = "https://www.instapaper.com/api/1/bookmarks/list"
    request_data = {
        "limit": settings.INSTAPAPER_LIMIT
    }

    if folder_name is not None:
        request_data.folder_id = folder_id

    response = session.post(url, data=request_data)
    # TODO: handle paging more than 500 bookmarks
    if response.status_code == 200:
        response_data = response.json()
        return response_data
    else:
        raise Exception(f"Failed to fetch bookmarks: {response.text}")


def create_instapaper_folder(session, folder_name):
    """Create a new Instapaper folder."""
    url = "https://www.instapaper.com/api/1/folders/add"
    response = session.post(url, data={"title": folder_name})
    if response.status_code == 200:
        return response.json()[0]["folder_id"]
    else:
        raise Exception(f"Failed to create folder: {response.text}")


def save_instapaper_bookmark(session, folder_id, url, title, description):
    """Save a bookmark to Instapaper."""
    api_url = "https://www.instapaper.com/api/1/bookmarks/add"
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


def generate_unique_folder_name(base_name):
    """Generate a unique folder name based on the base name."""
    unique_suffix = str(uuid.uuid4())[:4]  # Generate a short unique identifier
    return f"{base_name}-{unique_suffix}"
