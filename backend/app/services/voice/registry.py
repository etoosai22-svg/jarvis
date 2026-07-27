"""VOICE_PROVIDER 설정에 따라 STT/TTS 구현을 고른다."""

from __future__ import annotations

import sys

from app.core.config import Settings
from app.services.voice.base import SpeechToText, TextToSpeech


def _resolve(settings: Settings) -> str:
    provider = (settings.voice_provider or "auto").lower()
    if provider != "auto":
        return provider
    if settings.voice_api_key:
        return "openai"
    return "local" if sys.platform == "darwin" else "none"


def get_stt(settings: Settings) -> SpeechToText | None:
    """None이면 음성 인식 비활성 — 호출자는 자리표시 응답을 낸다."""
    provider = _resolve(settings)
    if provider == "openai":
        from app.services.voice.openai_provider import OpenAISpeechToText

        return OpenAISpeechToText(settings.voice_api_key, settings.openai_whisper_model)
    if provider == "local":
        from app.services.voice.local import LocalSpeechToText

        return LocalSpeechToText(
            model_size=settings.local_whisper_model,
            language=settings.voice_language,
        )
    return None


def get_tts(settings: Settings) -> TextToSpeech | None:
    provider = _resolve(settings)
    if provider == "openai":
        from app.services.voice.openai_provider import OpenAITextToSpeech

        return OpenAITextToSpeech(
            settings.voice_api_key, settings.openai_tts_model, settings.openai_tts_voice
        )
    if provider == "local":
        from app.services.voice.local import MacSayTextToSpeech

        return MacSayTextToSpeech(voice=settings.local_tts_voice)
    return None


def describe_voice(settings: Settings) -> dict[str, str | None]:
    """헬스체크/디버그용. 키는 포함하지 않는다."""
    stt, tts = get_stt(settings), get_tts(settings)
    return {
        "provider": _resolve(settings),
        "stt": getattr(stt, "name", None),
        "tts": getattr(tts, "name", None),
    }
