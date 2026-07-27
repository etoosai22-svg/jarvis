import type { MemoryDto, TaskDto, TaskStatusDto } from '@/types/api';
import type { JarvisTask, MemoryItem, TaskState } from '@/types/models';

/** 백엔드 상태값은 7종, 화면 상태값은 6종이라 planning/waiting_for_approval을 접는다. */
const TASK_STATE_BY_DTO: Record<TaskStatusDto, TaskState> = {
  queued: 'queued',
  planning: 'running',
  waiting_for_approval: 'approval_required',
  running: 'running',
  completed: 'completed',
  failed: 'failed',
  cancelled: 'cancelled',
};

const TASK_STATE_TO_DTO: Record<TaskState, TaskStatusDto> = {
  queued: 'queued',
  running: 'running',
  approval_required: 'waiting_for_approval',
  completed: 'completed',
  failed: 'failed',
  cancelled: 'cancelled',
};

const DEFAULT_SUBTITLE: Record<TaskState, string> = {
  queued: '대기 중입니다.',
  running: '처리 중입니다.',
  approval_required: '실행 전 확인이 필요합니다.',
  completed: '완료되었습니다.',
  failed: '실패했습니다. 다시 시도할 수 있어요.',
  cancelled: '취소되었습니다.',
};

export function toTaskState(status: TaskStatusDto): TaskState {
  return TASK_STATE_BY_DTO[status] ?? 'queued';
}

export function toTaskStatusDto(state: TaskState): TaskStatusDto {
  return TASK_STATE_TO_DTO[state];
}

export function toJarvisTask(dto: TaskDto): JarvisTask {
  const status = toTaskState(dto.status);
  return {
    id: dto.id,
    title: dto.title,
    subtitle: dto.description?.trim() || DEFAULT_SUBTITLE[status],
    status,
    progress: status === 'completed' ? 100 : undefined,
  };
}

export function toMemoryItem(dto: MemoryDto): MemoryItem {
  return {
    id: dto.id,
    title: dto.title?.trim() || dto.content.slice(0, 40),
    content: dto.content,
    source: `${dto.category} · ${formatRelativeTime(dto.updated_at)}`,
    suggested: dto.confidence < 0.6,
  };
}

/** 백엔드는 tz 표기 없는 UTC 문자열을 준다 — 파싱 전에 Z를 붙인다. */
export function parseServerDate(value: string): Date {
  const normalized = /[zZ]|[+-]\d{2}:?\d{2}$/.test(value) ? value : `${value}Z`;
  return new Date(normalized);
}

export function formatRelativeTime(value: string, now: Date = new Date()): string {
  const date = parseServerDate(value);
  if (Number.isNaN(date.getTime())) return '시간 정보 없음';

  const diffMinutes = Math.floor((now.getTime() - date.getTime()) / 60_000);
  if (diffMinutes < 1) return '방금 전';
  if (diffMinutes < 60) return `${diffMinutes}분 전`;

  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24) return `${diffHours}시간 전`;

  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 30) return `${diffDays}일 전`;
  return date.toLocaleDateString('ko-KR');
}
