from pydantic import BaseModel

class CacheConfig(BaseModel):
    """Backend cache configuration parameters.

    Attributes:
        url: cache URL, if there is a single string.
        host: cache host.
        port: cache port.
        ttl: cache TTL.
        use_cache: whether or not to use the cache at all
        skip_cache: retrieve new data, whether or not data is cached
        overwrite_cache: overwrite the cache with the current result, regardless of expiration
    """

    url: str | None = None
    host: str | None = None
    port: int | None = None
    ttl: int = 300
    use_cache: bool | None = True
    skip_cache: bool | None = False
    overwrite_cache: bool | None = False

