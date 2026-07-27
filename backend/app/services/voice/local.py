"""온디바이스 음성 — faster-whisper(STT) + macOS `say`(TTS).

키가 필요 없고 오디오가 기기를 떠나지 않는다 (Part 19 개인정보 원칙).
"""

from __future__ import annotations

import asyncio
import logging
import shutil
from functools import lru_cache
from tempfile import TemporaryDirectory
from pathlib import Path

from app.services.voice.base import VoiceUnavailable

logger = logging.getLogger(__name__)


@lru_cache(maxsize=2)
def _load_model(model_size: str, compute_type: str):
    """모델 로딩은 비싸다 — 크기별로 한 번만 만들고 재사용한다."""
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:  # pragma: no cover - 선택 의존성
        raise VoiceUnavailable(
            "faster-whisper가 설치되지 않았습니다. `uv sync --extra voice`로 설치하세요."
        ) from exc
    return WhisperModel(model_size, device="cpu", compute_type=compute_type)


class LocalSpeechToText:
    name = "local:faster-whisper"

    def __init__(self, model_size: str = "base", language: str = "ko", compute_type: str = "int8") -> None:
        self._model_size = model_size
        self._language = language
        self._compute_type = compute_type

    def _transcribe_sync(self, path: str) -> str:
        model = _load_model(self._model_size, self._compute_type)
        segments, _info = model.transcribe(path, language=self._language, vad_filter=True)
        return " ".join(segment.text.strip() for segment in segments).strip()

    async def transcribe(self, audio: bytes, filename: str = "audio.wav") -> str:
        if not audio:
            raise VoiceUnavailable("빈 오디오입니다.")
        suffix = Path(filename).suffix or ".wav"
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / f"input{suffix}"
            path.write_bytes(audio)
            # 모델 추론은 blocking이므로 이벤트 루프를 막지 않게 스레드로 넘긴다.
            return await asyncio.to_thread(self._transcribe_sync, str(path))


class MacSayTextToSpeech:
    """macOS 내장 TTS. 한국어 음성(Yuna 등)을 그대로 쓴다.

    `say`는 무압축 AIFF를 낸다 — 문장 하나가 수 MB라 WebSocket 프레임 한도(1MB)를
    넘긴다. ffmpeg가 있으면 AAC로 압축해 보낸다 (수십 배 작아진다).
    """

    name = "local:say"

    def __init__(self, voice: str = "Yuna", rate: int = 190, bitrate: str = "48k") -> None:
        self._voice = voice
        self._rate = rate
        self._bitrate = bitrate
        self._compress = shutil.which("ffmpeg") is not None

    @property
    def media_type(self) -> str:
        return "audio/mp4" if self._compress else "audio/aiff"

    async def _run(self, *argv: str) -> bytes | None:
        process = await asyncio.create_subprocess_exec(
            *argv, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE
        )
        _, stderr = await process.communicate()
        return None if process.returncode != 0 else stderr

    async def synthesize(self, text: str) -> bytes:
        if shutil.which("say") is None:
            raise VoiceUnavailable("`say`를 찾을 수 없습니다 (macOS 전용).")
        if not text.strip():
            raise VoiceUnavailable("빈 텍스트입니다.")

        with TemporaryDirectory() as tmp:
            raw = Path(tmp) / "speech.aiff"
            if await self._run("say", "-v", self._voice, "-r", str(self._rate), "-o", str(raw), text) is None:
                raise VoiceUnavailable("say 실행에 실패했습니다.")
            if not raw.exists():
                raise VoiceUnavailable("say가 오디오를 만들지 못했습니다.")

            if not self._compress:
                return raw.read_bytes()

            encoded = Path(tmp) / "speech.m4a"
            ok = await self._run(
                "ffmpeg", "-y", "-i", str(raw), "-c:a", "aac", "-b:a", self._bitrate,
                "-ac", "1", str(encoded), "-loglevel", "error",
            )
            # 압축이 실패하면 원본이라도 돌려준다 (음성이 끊기는 것보다 낫다).
            return encoded.read_bytes() if ok is not None and encoded.exists() else raw.read_bytes()
