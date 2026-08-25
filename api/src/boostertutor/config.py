"""Application settings, loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    database_url: str
    frontend_origin: str = "http://localhost:5173"

    @property
    def sqlalchemy_url(self) -> str:
        """Supabase hands out `postgresql://`, which SQLAlchemy reads as
        "use psycopg2". We installed psycopg 3, so name the driver explicitly."""
        url = self.database_url
        for prefix in ("postgresql://", "postgres://"):
            if url.startswith(prefix):
                return url.replace(prefix, "postgresql+psycopg://", 1)
        return url


settings = Settings()