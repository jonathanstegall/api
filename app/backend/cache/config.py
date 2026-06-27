from pydantic import BaseModel

class CacheConfig(BaseModel):
    """Backend cache configuration parameters.

    Attributes:
        url: cache URL, if there is a single string.
        host: cache host.
        port: cache port.
        ttl: cache TTL.
    """

    url: str | None = None
    host: str | None = None
    port: int | None = None
    ttl: int = 300

