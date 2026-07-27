"""음성 제공자 (Part 6).

STT/TTS는 LLM과 별개 공급자다 — Bedrock 게이트웨이는 채팅만 중계하므로
음성은 온디바이스(기본) 또는 OpenAI로 처리한다. `VOICE_PROVIDER`로 고른다:

- `auto`   : OpenAI 키가 있으면 openai, 없으면 local (기본)
- `local`  : faster-whisper(STT) + macOS `say`(TTS). 키 불필요, 데이터가 기기를 떠나지 않는다
- `openai` : Whisper + OpenAI TTS
- `none`   : 음성 비활성 (자리표시 응답)
"""

from app.services.voice.base import SpeechToText, TextToSpeech, VoiceUnavailable
from app.services.voice.registry import get_stt, get_tts, describe_voice

__all__ = ["SpeechToText", "TextToSpeech", "VoiceUnavailable", "get_stt", "get_tts", "describe_voice"]
