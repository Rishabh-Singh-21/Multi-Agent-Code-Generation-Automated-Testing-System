from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Agent Backend"
    app_version: str = "1.0.0"
    debug: bool = False
    api_prefix: str = "/api/v1"
    log_level: str = "INFO"
    retry_attempts: int = 3
    retry_base_delay: float = 0.25

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
