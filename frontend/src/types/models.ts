export type VoiceState = 'idle' | 'preparing' | 'listening' | 'transcribing' | 'thinking' | 'executing' | 'speaking' | 'error';
export type TaskState = 'queued' | 'running' | 'approval_required' | 'completed' | 'failed' | 'cancelled';
export type MemoryCategory = '선호' | '사람·관계' | '프로젝트' | '반복 일정' | '서비스';

export interface Message {
  id: string;
  role: 'assistant' | 'user';
  content: string;
  streaming?: boolean;
  partial?: boolean;
}

export interface JarvisTask {
  id: string;
  title: string;
  subtitle: string;
  status: TaskState;
  progress?: number;
  service?: string;
}

export interface MemoryItem {
  id: string;
  title: string;
  content: string;
  source: string;
  suggested?: boolean;
}

export interface Integration {
  id: string;
  title: string;
  subtitle: string;
  status: 'connected' | 'expired' | 'disconnected' | 'error';
}
