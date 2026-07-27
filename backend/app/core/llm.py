"""LLM 클라이언트 팩토리.

JARVIS는 OpenAI **프로토콜**로 말하지만, 상대는 OpenAI일 수도 있고
OpenAI 호환 게이트웨이(예: openclaw의 Bedrock 브리지)일 수도 있다.
`LLM_BASE_URL`만 바꾸면 같은 코드로 양쪽을 쓴다 —
게이트웨이가 openai-completions 규약을 그대로 말하므로 SDK 교체는 필요 없다.
"""

from __future__ import annotations

from openai import AsyncOpenAI

from app.core.config import Settings


def build_client(settings: Settings) -> AsyncOpenAI | None:
    """LLM 클라이언트. 키가 없으면 None (호출자는 규칙 기반으로 폴백한다)."""
    if not settings.llm_api_key:
        return None
    kwargs: dict[str, object] = {"api_key": settings.llm_api_key}
    if settings.llm_base_url:
        kwargs["base_url"] = settings.llm_base_url
    return AsyncOpenAI(**kwargs)  # type: ignore[arg-type]


def describe_provider(settings: Settings) -> str:
    """로그·헬스체크용 표기 (키는 절대 포함하지 않는다)."""
    if not settings.llm_api_key:
        return "none"
    return f"{settings.llm_base_url or 'https://api.openai.com/v1'} · {settings.llm_chat_model}"
