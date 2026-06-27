from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)

from app.backend.database.config import DatabaseConfig


class Config(BaseSettings):
    """API configuration parameters.

    Automatically read modifications to the configuration parameters
    from environment variables and ``.env`` file.

    Attributes:
        database:
            Database configuration settings.
            Instance of :class:`app.backend.config.DatabaseConfig`.
        token_key:
            Random secret key used to sign JWT tokens.
    """

    database: DatabaseConfig = DatabaseConfig()
    token_key: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra='ignore'
    )

config = Config()
