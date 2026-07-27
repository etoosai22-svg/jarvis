"""OpenAI 음성 — Whisper(STT) + OpenAI TTS. VOICE_API_KEY가 필요하다."""

from __future__ import annotations

from tempfile import NamedTemporaryFile

from openai import AsyncOpenAI

from app.services.voice.base import VoiceUnavailable


class OpenAISpeechToText:
    name = "openai:whisper"

    def __init__(self, api_key: str | None, model: str) -> None:
        self._api_key = api_key
        self._model = model

    async def transcribe(self, audio: bytes, filename: str = "audio.wav") -> str:
        if not self._api_key:
            raise VoiceUnavailable("VOICE_API_KEY가 없습니다.")
        if not audio:
            raise VoiceUnavailable("빈 오디오입니다.")
        client = AsyncOpenAI(api_key=self._api_key)
        suffix = ".wav" if filename.endswith(".wav") else ".webm"
        with NamedTemporaryFile(suffix=suffix) as temp:
            temp.write(audio)
            temp.flush()
            with open(temp.name, "rb") as handle:
                result = await client.audio.transcriptions.create(model=self._model, file=handle)
        return (getattr(result, "text", "") or "").strip()


class OpenAITextToSpeech:
    name = "openai:tts"
    media_type = "audio/mpeg"

    def __init__(self, api_key: str | None, model: str, voice: str) -> None:
        self._api_key = api_key
        self._model = model
        self._voice = voice

    async def synthesize(self, text: str) -> bytes:
        if not self._api_key:
            raise VoiceUnavailable("VOICE_API_KEY가 없습니다.")
        client = AsyncOpenAI(api_key=self._api_key)
        speech = await client.audio.speech.create(model=self._model, voice=self._voice, input=text)
        return speech.content
