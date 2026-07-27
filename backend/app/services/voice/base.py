"""음성 제공자 인터페이스."""

from __future__ import annotations

from typing import Protocol


class VoiceUnavailable(RuntimeError):
    """이 환경에서 해당 제공자를 쓸 수 없다 (미설치, 키 없음 등)."""


class SpeechToText(Protocol):
    name: str

    async def transcribe(self, audio: bytes, filename: str = "audio.wav") -> str:
        """오디오 바이트를 텍스트로. 실패 시 VoiceUnavailable을 던진다."""
        ...


class TextToSpeech(Protocol):
    name: str
    #: 반환 오디오의 MIME 타입 (앱이 재생기를 고를 때 쓴다)
    media_type: str

    async def synthesize(self, text: str) -> bytes:
        """텍스트를 오디오 바이트로. 실패 시 VoiceUnavailable을 던진다."""
        ...
