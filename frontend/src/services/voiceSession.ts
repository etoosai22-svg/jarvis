import { jarvisApi } from '@/services/api';
import type { VoiceSocketEvent } from '@/types/api';

/**
 * `WS /api/v1/ws/voice` 한 턴의 프로토콜 처리 (docs/09 §3).
 *
 * 네이티브 오디오 모듈에 의존하지 않는다 — 재생은 `onAudio` 콜백으로 위임한다.
 * 덕분에 브라우저·테스트에서 이 경로를 그대로 실행해 볼 수 있다.
 */

/** WS 한 턴에서 관찰한 결과. 스토어가 화면 상태로 옮긴다. */
export type VoiceTurn = {
  transcript?: string;
  reply?: string;
  taskStatus?: string;
  /** 도구 실행·승인 요청 등 서버가 알려준 부수효과 */
  sawAction: boolean;
};

export type VoiceSessionHandlers = {
  onTranscript?: (text: string, final: boolean) => void;
  onReply?: (text: string) => void;
  onAction?: (event: VoiceSocketEvent) => void;
  onAudio?: (audioBase64: string, mediaType?: string) => void;
  onError?: (message: string) => void;
};

export function runVoiceTurn(
  sessionId: string,
  audioBase64: string,
  handlers: VoiceSessionHandlers = {},
): Promise<VoiceTurn> {
  return new Promise<VoiceTurn>((resolve, reject) => {
    const turn: VoiceTurn = { sawAction: false };
    let settled = false;

    const finish = (error?: Error) => {
      if (settled) return;
      settled = true;
      jarvisApi.disconnectVoiceSocket();
      if (error) reject(error);
      else resolve(turn);
    };

    jarvisApi.connectVoiceSocket(sessionId, {
      onEvent: (event) => {
        switch (event.type) {
          case 'task.started':
            jarvisApi.sendVoiceEvent({ type: 'audio.chunk', audio: audioBase64 });
            jarvisApi.sendVoiceEvent({ type: 'audio.end' });
            break;

          case 'transcript.partial':
            handlers.onTranscript?.(event.text, false);
            break;

          case 'transcript.final':
            turn.transcript = event.text;
            handlers.onTranscript?.(event.text, true);
            break;

          case 'assistant.delta':
            turn.reply = event.text;
            handlers.onReply?.(event.text);
            break;

          case 'task.progress':
          case 'approval.required':
            turn.sawAction = true;
            handlers.onAction?.(event);
            break;

          case 'audio.output':
            if (event.format === 'base64') {
              handlers.onAudio?.(event.audio, event.media_type);
            }
            break;

          case 'task.completed':
            turn.taskStatus = event.status;
            finish();
            break;

          case 'error':
            handlers.onError?.(event.message);
            finish(new Error(event.message));
            break;
        }
      },
      onError: () => finish(new Error('음성 서버에 연결하지 못했습니다.')),
      onClose: () => finish(settled ? undefined : new Error('음성 연결이 끊어졌습니다.')),
    });
  });
}
