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

    """

    app_name: str = "Open API"
    app_description: str = ""
    app_version: str = ""

    token_key: str = ""
    token_type: str = ""
    secret_key: str = ""
    token_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    database: DatabaseConfig = DatabaseConfig()
    cache: CacheConfig = CacheConfig()
    raindrop: RaindropConfig = RaindropConfig()
    tumblr: TumblrConfig = TumblrConfig()
    instapaper: InstapaperConfig = InstapaperConfig()

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra='ignore'
    )

config = Config()
