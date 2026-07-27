from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "JARVIS Backend"
    environment: str = "local"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    openai_chat_model: str = "gpt-4o"
    openai_tts_model: str = "gpt-4o-mini-tts"
    openai_tts_voice: str = "alloy"
    openai_whisper_model: str = "whisper-1"

    database_url: str = "sqlite+aiosqlite:///./jarvis.db"
    redis_url: str = "redis://localhost:6379/0"

    cors_origins: str = "http://localhost:3000,http://localhost:8081,http://127.0.0.1:8081"
    oauth_issuer_url: str | None = None
    oauth_audience: str | None = None
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
