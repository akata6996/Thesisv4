"""Application settings loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AEGIS Gateway API"
    app_env: str = "dev"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    database_url: str = "sqlite:///./aegis.db"
    sql_echo: bool = False

    auth_secret_key: str = "change-me"
    auth_algorithm: str = "HS256"
    auth_access_token_expire_minutes: int = 30

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
