from pydantic import BaseModel

class RaindropConfig(BaseModel):
    """External API integration parameters.

    Attributes:
        client_id: client ID
        client_secret: client secret
        access_token: access token
        limit: limit of results to return
    """

    client_id: str | None = None
    client_secret: str | None = None
    access_token: str | None = None
    limit: int = 50

class TumblrConfig(BaseModel):
    """External API integration parameters.

    Attributes:
        consumer_key: consumer key
        consumer_secret: consumer secret
        blog_id: blog ID
        limit: limit of results to return
    """

    consumer_key: str | None = None
    consumer_secret: str | None = None
    blog_id: str | None = None
    limit: int = 25


class InstapaperConfig(BaseModel):
    """External API integration parameters.

    Attributes:
        consumer_key: consumer key
        consumer_secret: consumer secret
        username: account username
        password: account password
        limit: limit of results to return
    """

    consumer_key: str | None = None
    consumer_secret: str | None = None
    username: str | None = None
    password: str | None = None
    limit: int = 25

