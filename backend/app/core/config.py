from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# app/core/config.py -> app/core -> app -> backend -> 저장소 루트
REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    app_name: str = "JARVIS Backend"
    environment: str = "local"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # LLM — OpenAI 프로토콜로 말하되 상대는 교체 가능하다.
    # openclaw의 Bedrock 브리지처럼 OpenAI 호환 게이트웨이면 LLM_BASE_URL만 지정한다.
    # (OPENAI_API_KEY도 계속 인식 — 기존 설정 호환)
    llm_api_key: str | None = Field(
        default=None, validation_alias=AliasChoices("LLM_API_KEY", "OPENAI_API_KEY")
    )
    llm_base_url: str | None = Field(
        default=None, validation_alias=AliasChoices("LLM_BASE_URL", "OPENAI_BASE_URL")
    )
    llm_chat_model: str = Field(
        default="gpt-4o", validation_alias=AliasChoices("LLM_CHAT_MODEL", "OPENAI_CHAT_MODEL")
    )
    llm_max_tokens: int = 4096
    # Claude Opus 4.7 / Sonnet 5 이후 sampling 파라미터는 API에서 제거되어 400을 낸다.
    # 기본은 미전송. OpenAI 계열을 쓸 때만 값을 넣는다.
    llm_temperature: float | None = None

    # 음성 — 현재는 OpenAI 전용 (Bedrock 게이트웨이는 STT/TTS를 제공하지 않는다)
    voice_api_key: str | None = Field(
        default=None, validation_alias=AliasChoices("VOICE_API_KEY", "OPENAI_API_KEY")
    )
    # auto | local | openai | none  (auto = 키 있으면 openai, macOS면 local)
    voice_provider: str = "auto"
    voice_language: str = "ko"
    openai_tts_model: str = "gpt-4o-mini-tts"
    openai_tts_voice: str = "alloy"
    openai_whisper_model: str = "whisper-1"
    # 온디바이스 설정 (tiny/base/small/medium/large-v3 — base가 속도·정확도 균형)
    local_whisper_model: str = "base"
    local_tts_voice: str = "Yuna"

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

    # populate_by_name: validation_alias가 걸린 필드(openai_api_key)를 필드명으로도
    # 지정할 수 있게 한다. 없으면 Settings(openai_api_key=...)가 조용히 무시된다.
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", populate_by_name=True
    )

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
