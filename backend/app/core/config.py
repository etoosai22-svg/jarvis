from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# app/core/config.py -> app/core -> app -> backend -> 저장소 루트
REPO_ROOT = Path(__file__).resolve().parents[3]


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
    # 로컬 SQLite 편의용. Postgres에서는 false로 두고 `alembic upgrade head`를 쓴다.
    auto_create_tables: bool = True

    cors_origins: str = "http://localhost:3000,http://localhost:8081,http://127.0.0.1:8081"

    # 인증. auth_required=False면 개발용 로컬 사용자로 동작한다.
    auth_required: bool = False
    oauth_issuer_url: str | None = None
    oauth_audience: str | None = None
    oauth_jwks_url: str | None = None
    dev_user_id: str = "local-user"

    # 대화 컨텍스트
    system_prompt_path: str = str(REPO_ROOT / "prompts" / "system_prompt.md")
    chat_history_limit: int = 12
    chat_memory_limit: int = 5

    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def resolved_jwks_url(self) -> str | None:
        if self.oauth_jwks_url:
            return self.oauth_jwks_url
        if self.oauth_issuer_url:
            return f"{self.oauth_issuer_url.rstrip('/')}/.well-known/jwks.json"
        return None


@lru_cache
def get_settings() -> Settings:
    return Settings()
