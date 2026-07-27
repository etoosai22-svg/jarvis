"""음성 입출력 (Part 6).

WS는 자리표시 문구가 아니라 실제 파이프라인을 돈다:
  audio.chunk* → audio.end → STT → 오케스트레이터(도구·승인) → TTS
"""

from __future__ import annotations

import base64
import binascii
import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from app.core.config import Settings, get_settings
from app.core.database import AsyncSessionLocal
from app.services.chat_service import handle_chat
from app.services.voice import describe_voice, get_stt, get_tts

logger = logging.getLogger(__name__)
router = APIRouter()

TRANSCRIPT_UNAVAILABLE = "음성 입력을 수신했습니다."
MAX_AUDIO_BYTES = 25 * 1024 * 1024


class VoiceResponse(BaseModel):
    transcript: str
    intent: str
    tts_audio_base64: str | None = None
    tts_media_type: str | None = None


def _infer_intent(transcript: str) -> str:
    return "task" if any(word in transcript for word in ("해줘", "일정", "회의", "작업", "등록")) else "chat"


async def _transcribe(settings: Settings, audio: bytes, filename: str) -> str:
    """실패해도 예외를 올리지 않는다 — 음성이 안 돼도 대화는 계속되어야 한다."""
    stt = get_stt(settings)
    if stt is None:
        return TRANSCRIPT_UNAVAILABLE
    try:
        return (await stt.transcribe(audio, filename)) or TRANSCRIPT_UNAVAILABLE
    except Exception as exc:
        logger.warning("STT failed (%s): %s", getattr(stt, "name", "?"), exc)
        return TRANSCRIPT_UNAVAILABLE


async def _speak(settings: Settings, text: str) -> tuple[str | None, str | None]:
    tts = get_tts(settings)
    if tts is None or not text.strip():
        return None, None
    try:
        audio = await tts.synthesize(text)
    except Exception as exc:
        logger.warning("TTS failed (%s): %s", getattr(tts, "name", "?"), exc)
        return None, None
    return base64.b64encode(audio).decode("ascii"), tts.media_type


@router.get("/voice/health")
async def voice_health(settings: Annotated[Settings, Depends(get_settings)]) -> dict[str, Any]:
    """어떤 음성 제공자가 활성인지 — 키 없이 확인 가능."""
    return describe_voice(settings)


@router.post("/voice", response_model=VoiceResponse)
async def create_voice(
    settings: Annotated[Settings, Depends(get_settings)],
    file: UploadFile = File(...),
) -> VoiceResponse:
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="empty audio file")
    if len(data) > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="audio too large")

    transcript = await _transcribe(settings, data, file.filename or "audio.wav")
    audio_b64, media_type = await _speak(settings, transcript)
    return VoiceResponse(
        transcript=transcript,
        intent=_infer_intent(transcript),
        tts_audio_base64=audio_b64,
        tts_media_type=media_type,
    )


@router.websocket("/ws/voice")
async def voice_websocket(websocket: WebSocket) -> None:
    """음성 대화 루프. 이벤트 계약은 docs/09 §3."""
    settings = get_settings()
    await websocket.accept()

    session_id = "anonymous"
    user_id = settings.dev_user_id  # WS 인증은 Phase 7 대상
    chunks: list[bytes] = []

    async def send(event_type: str, **fields: Any) -> None:
        await websocket.send_json({"type": event_type, **fields})

    try:
        while True:
            event: dict[str, Any] = await websocket.receive_json()
            event_type = event.get("type")

            if event_type == "session.start":
                session_id = str(event.get("session_id") or "anonymous")
                chunks.clear()
                await send("task.started", session_id=session_id)

            elif event_type == "audio.chunk":
                raw = str(event.get("audio") or event.get("data") or "")
                try:
                    chunks.append(base64.b64decode(raw, validate=True))
                except (binascii.Error, ValueError):
                    await send("error", message="audio.chunk는 base64여야 합니다.")
                    continue
                await send("transcript.partial", text="듣고 있습니다...", chunk_count=len(chunks))

            elif event_type == "audio.end":
                audio = b"".join(chunks)
                chunks.clear()
                transcript = await _transcribe(settings, audio, "stream.wav")
                await send("transcript.final", text=transcript)

                # 문장이 완성되는 대로 말한다 — 응답 전체를 기다리지 않는다 (docs/09 §3).
                sent_actions: set[str] = set()

                async def emit_action(action: dict[str, Any]) -> None:
                    """액션은 발생 즉시 나간다. 스트리밍에서는 턴이 끝나야 볼 수 있는
                    반환값에 의존할 수 없다 (그렇게 했다가 이벤트가 통째로 유실됐다)."""
                    key = f"{action.get('type')}:{action.get('request_id') or action.get('task_id')}"
                    if key in sent_actions:
                        return
                    sent_actions.add(key)
                    # action에 이미 type·status가 있으므로 splat하지 않는다
                    # (send()의 인자와 충돌해 TypeError가 난다).
                    detail = {key_: value for key_, value in action.items() if key_ != "type"}
                    if action.get("type") == "approval.required":
                        await send("approval.required", **detail)
                    else:
                        detail.setdefault("status", "running")
                        await send("task.progress", **detail)

                async def speak_sentence(sentence: str) -> None:
                    await send("assistant.delta", text=sentence)
                    audio_b64, media_type = await _speak(settings, sentence)
                    if audio_b64:
                        await send("audio.output", format="base64", media_type=media_type, audio=audio_b64)

                if transcript == TRANSCRIPT_UNAVAILABLE:
                    reply = "죄송합니다, 실장님. 음성을 인식하지 못했습니다."
                    task_status, streamed, actions = "failed", False, []
                else:
                    async with AsyncSessionLocal() as db:
                        result = await handle_chat(
                            db=db,
                            settings=settings,
                            user_id=user_id,
                            session_id=session_id,
                            user_message=transcript,
                            for_voice=True,
                            on_sentence=speak_sentence,
                            on_action=emit_action,
                        )
                    reply = result.reply
                    task_status, streamed, actions = result.task_status, result.streamed, result.actions

                # 규칙 라우터는 콜백을 쓰지 않는다 — 못 보낸 액션과 응답을 여기서 마저 낸다.
                for action in actions:
                    await emit_action(action)

                if not streamed:
                    await send("assistant.delta", text=reply)
                    audio_b64, media_type = await _speak(settings, reply)
                    if audio_b64:
                        await send("audio.output", format="base64", media_type=media_type, audio=audio_b64)
                    else:
                        await send("audio.output", format="text", text=reply)

                await send("task.completed", status=task_status)

            elif event_type == "task.cancel":
                chunks.clear()
                await send("task.completed", status="cancelled")

            elif event_type == "approval.respond":
                await send("task.progress", status="approval_received")

            else:
                await send("error", message=f"unsupported event: {event_type}")

    except WebSocketDisconnect:
        logger.info("voice websocket disconnected: session_id=%s", session_id)
