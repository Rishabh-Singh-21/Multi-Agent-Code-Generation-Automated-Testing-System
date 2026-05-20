from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Multi-Agent Code Generation + Automated Testing System"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    llm_provider: str = "openai"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-70b-versatile"
    database_url: str = "sqlite:///./data/sessions.db"
    generated_root: str = "generated_sessions"
    docker_image: str = "macgats-sandbox:latest"
    docker_timeout_seconds: int = 90
    max_retries: int = 3

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
Path("data").mkdir(exist_ok=True)
Path(settings.generated_root).mkdir(parents=True, exist_ok=True)
