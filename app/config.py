from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)

from app.backend.database.config import DatabaseConfig
from app.backend.cache.config import CacheConfig
from app.backend.ingest.config import RaindropConfig, TumblrConfig, InstapaperConfig

class Config(BaseSettings):
    """API configuration parameters.

    Automatically read modifications to the configuration parameters
    from environment variables and ``.env`` file.

    Attributes:
        database: Instance of :class:`app.backend.database.config.DatabaseConfig`.
        cache: Instance of :class:`app.backend.cache.config.CacheConfig`.
        raindrop: Instance of :class:`app.backend.cache.config.RaindropConfig`.
        tumblr: Instance of :class:`app.backend.cache.config.TumblrConfig`.
        instapaper: Instance of :class:`app.backend.cache.config.InstapaperConfig`.
        token_key: Random secret key used to sign JWT tokens.
    """

    database: DatabaseConfig = DatabaseConfig()
    cache: CacheConfig = CacheConfig()
    raindrop: RaindropConfig = RaindropConfig()
    tumblr: TumblrConfig = TumblrConfig()
    instapaper: InstapaperConfig = InstapaperConfig()
    token_key: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra='ignore'
    )

config = Config()
