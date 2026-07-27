/** 백엔드(`/api/v1/*`)가 그대로 주고받는 DTO. 앱 내부 모델은 `models.ts`를 쓴다. */

export type TaskStatusDto =
  | 'queued'
  | 'planning'
  | 'waiting_for_approval'
  | 'running'
  | 'completed'
  | 'failed'
  | 'cancelled';

export interface TaskDto {
  id: string;
  user_id: string | null;
  title: string;
  description: string | null;
  status: TaskStatusDto;
  priority: number;
  /** 승인 대기 중인 MCP 호출 JSON — {server,tool,arguments} (docs/09) */
  payload: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface TaskCreateDto {
  title: string;
  description?: string | null;
  user_id?: string | null;
  priority?: number;
}

export interface MemoryDto {
  id: string;
  user_id: string | null;
  category: string;
  title: string | null;
  content: string;
  embedding_id: string | null;
  confidence: number;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface MemoryCreateDto {
  category?: string;
  content: string;
  title?: string | null;
  user_id?: string | null;
  confidence?: number;
  tags?: string[];
}

export interface ChatRequestDto {
  session_id: string;
  message: string;
  metadata?: Record<string, unknown>;
}

export interface ChatResponseDto {
  reply: string;
  task_status: string;
  actions: Record<string, unknown>[];
}

export interface VoiceResponseDto {
  transcript: string;
  intent: string;
  tts_audio_base64: string | null;
}

/**
 * `WS /api/v1/ws/voice` 이벤트.
 * 백엔드는 payload로 감싸지 않고 필드를 최상위에 펼쳐서 보낸다.
 */
export type VoiceSocketEvent =
  | { type: 'session.start'; session_id: string }
  | { type: 'audio.chunk'; audio: string }
  | { type: 'audio.end' }
  | { type: 'task.cancel' }
  | { type: 'approval.respond'; approved: boolean }
  | { type: 'task.started'; session_id: string }
  | { type: 'transcript.partial'; text: string; chunk_count: number }
  | { type: 'transcript.final'; text: string }
  | { type: 'assistant.delta'; text: string }
  | { type: 'audio.output'; format: string; text: string }
  | { type: 'task.progress'; status: string }
  | { type: 'task.completed'; status: string }
  | { type: 'error'; message: string };
