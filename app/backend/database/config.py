from pydantic import BaseModel

class DatabaseConfig(BaseModel):
    """Backend database configuration parameters.

    Attributes:
        dsn:
            DSN for target database.
    """

    dsn: str = "postgresql://user:password@host:port/dbname"
    dialect: str = "postgresql"
    host: str = "host"
    port: int | None = None
    user: str = "user"
    password: str | None = None
    name: str = "name"

