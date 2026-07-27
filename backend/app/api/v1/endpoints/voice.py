import base64
import logging
from tempfile import NamedTemporaryFile
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from openai import AsyncOpenAI
from pydantic import BaseModel

from app.core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()


class VoiceResponse(BaseModel):
    transcript: str
    intent: str
    tts_audio_base64: str | None = None


def _infer_intent(transcript: str) -> str:
    return "task" if any(word in transcript for word in ["해줘", "일정", "회의", "작업", "등록"]) else "chat"


@router.post("/voice", response_model=VoiceResponse)
async def create_voice(file: UploadFile = File(...)) -> VoiceResponse:
    settings = get_settings()
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="empty audio file")

    transcript = "음성 입력을 수신했습니다."
    tts_audio_base64: str | None = None

    if settings.voice_api_key:
        try:
            client = AsyncOpenAI(api_key=settings.voice_api_key)
            suffix = ".wav" if file.filename and file.filename.endswith(".wav") else ".webm"
            with NamedTemporaryFile(suffix=suffix) as temp:
                temp.write(data)
                temp.flush()
                with open(temp.name, "rb") as audio_file:
                    transcription = await client.audio.transcriptions.create(
                        model=settings.openai_whisper_model,
                        file=audio_file,
                    )
            transcript = getattr(transcription, "text", None) or transcript
            speech = await client.audio.speech.create(
                model=settings.openai_tts_model,
                voice=settings.openai_tts_voice,
                input=transcript,
            )
            tts_audio_base64 = base64.b64encode(speech.content).decode("ascii")
        except Exception as exc:  # pragma: no cover - external API/network dependent
            logger.exception("OpenAI voice call failed; using fallback", exc_info=exc)

    return VoiceResponse(transcript=transcript, intent=_infer_intent(transcript), tts_audio_base64=tts_audio_base64)


@router.websocket("/ws/voice")
async def voice_websocket(websocket: WebSocket) -> None:
    await websocket.accept()
    chunks: list[str] = []
    session_id: str | None = None
    try:
        while True:
            event: dict[str, Any] = await websocket.receive_json()
            event_type = event.get("type")
            if event_type == "session.start":
                session_id = str(event.get("session_id") or "anonymous")
                await websocket.send_json({"type": "task.started", "session_id": session_id})
            elif event_type == "audio.chunk":
                chunk = str(event.get("audio") or event.get("data") or "")
                chunks.append(chunk)
                await websocket.send_json({"type": "transcript.partial", "text": "듣고 있습니다...", "chunk_count": len(chunks)})
            elif event_type == "audio.end":
                transcript = "음성 스트림을 수신했습니다."
                await websocket.send_json({"type": "transcript.final", "text": transcript})
                await websocket.send_json({"type": "assistant.delta", "text": "네, 실장님. 처리하겠습니다."})
                await websocket.send_json({"type": "audio.output", "format": "text", "text": "네, 실장님. 처리하겠습니다."})
                await websocket.send_json({"type": "task.completed", "status": "completed"})
            elif event_type == "task.cancel":
                await websocket.send_json({"type": "task.completed", "status": "cancelled"})
            elif event_type == "approval.respond":
                await websocket.send_json({"type": "task.progress", "status": "approval_received"})
            else:
                await websocket.send_json({"type": "error", "message": f"unsupported event: {event_type}"})
    except WebSocketDisconnect:
        logger.info("voice websocket disconnected: session_id=%s", session_id)
