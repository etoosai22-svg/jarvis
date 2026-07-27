import { API_BASE_URL, WS_BASE_URL } from '@/config/env';
import type {
  ChatRequestDto,
  ChatResponseDto,
  MemoryCreateDto,
  MemoryDto,
  TaskCreateDto,
  TaskDto,
  TaskStatusDto,
  VoiceResponseDto,
  VoiceSocketEvent,
} from '@/types/api';

const REQUEST_TIMEOUT_MS = 15_000;

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status?: number,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

type ApiClientOptions = {
  apiBaseUrl?: string;
  wsBaseUrl?: string;
  /** OAuth 도입 후 Bearer 토큰 공급자를 주입한다. */
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
};

class JarvisApiClient {
  private apiBaseUrl: string;
  private wsBaseUrl: string;
  private getAccessToken?: ApiClientOptions['getAccessToken'];
  private socket?: WebSocket;

  constructor(options: ApiClientOptions = {}) {
    this.apiBaseUrl = options.apiBaseUrl ?? API_BASE_URL;
    this.wsBaseUrl = options.wsBaseUrl ?? WS_BASE_URL;
    this.getAccessToken = options.getAccessToken;
  }

  setAccessTokenProvider(provider: ApiClientOptions['getAccessToken']) {
    this.getAccessToken = provider;
  }

  health(): Promise<{ status: string; service: string; environment: string }> {
    return this.request('/api/v1/health');
  }

  chat(request: ChatRequestDto): Promise<ChatResponseDto> {
    return this.request('/api/v1/chat', { method: 'POST', body: JSON.stringify(request) });
  }

  uploadVoice(audio: Blob | FormData, filename = 'input.wav'): Promise<VoiceResponseDto> {
    const body = audio instanceof FormData ? audio : new FormData();
    if (!(audio instanceof FormData)) {
      body.append('file', audio, filename);
    }
    return this.request('/api/v1/voice', { method: 'POST', body });
  }

  listTasks(userId?: string): Promise<TaskDto[]> {
    return this.request(`/api/v1/tasks${userId ? `?user_id=${encodeURIComponent(userId)}` : ''}`);
  }

  createTask(payload: TaskCreateDto): Promise<TaskDto> {
    return this.request('/api/v1/tasks', { method: 'POST', body: JSON.stringify(payload) });
  }

  updateTaskStatus(taskId: string, status: TaskStatusDto): Promise<TaskDto> {
    const path = `/api/v1/tasks/${encodeURIComponent(taskId)}?status_value=${status}`;
    return this.request(path, { method: 'PATCH' });
  }

  listMemory(params: { userId?: string; category?: string } = {}): Promise<MemoryDto[]> {
    const query = new URLSearchParams();
    if (params.userId) query.set('user_id', params.userId);
    if (params.category) query.set('category', params.category);
    const suffix = query.toString() ? `?${query}` : '';
    return this.request(`/api/v1/memory${suffix}`);
  }

  createMemory(payload: MemoryCreateDto): Promise<MemoryDto> {
    return this.request('/api/v1/memory', { method: 'POST', body: JSON.stringify(payload) });
  }

  searchMemory(query: string, limit = 10): Promise<MemoryDto[]> {
    return this.request('/api/v1/memory/search', {
      method: 'POST',
      body: JSON.stringify({ query, limit }),
    });
  }

  connectVoiceSocket(
    sessionId: string,
    handlers: {
      onEvent: (event: VoiceSocketEvent) => void;
      onError?: (event: Event) => void;
      onClose?: () => void;
    },
  ): WebSocket {
    this.disconnectVoiceSocket();

    const socket = new WebSocket(`${this.wsBaseUrl}/api/v1/ws/voice`);
    socket.onopen = () => this.sendVoiceEvent({ type: 'session.start', session_id: sessionId });
    socket.onmessage = (message) => {
      try {
        handlers.onEvent(JSON.parse(message.data as string) as VoiceSocketEvent);
      } catch {
        handlers.onEvent({ type: 'error', message: '잘못된 WebSocket 응답을 받았습니다.' });
      }
    };
    socket.onerror = (event) => handlers.onError?.(event);
    socket.onclose = () => {
      this.socket = undefined;
      handlers.onClose?.();
    };

    this.socket = socket;
    return socket;
  }

  sendVoiceEvent(event: VoiceSocketEvent) {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(event));
    }
  }

  disconnectVoiceSocket() {
    if (this.socket) {
      this.socket.onclose = null;
      this.socket.close();
      this.socket = undefined;
    }
  }

  private async request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const token = await this.getAccessToken?.();
    const headers = new Headers(init.headers);

    // FormData는 boundary 포함 Content-Type을 런타임이 직접 채워야 한다.
    if (init.body !== undefined && !(init.body instanceof FormData)) {
      headers.set('Content-Type', 'application/json');
    }
    if (token) {
      headers.set('Authorization', `Bearer ${token}`);
    }

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

    let response: Response;
    try {
      response = await fetch(`${this.apiBaseUrl}${path}`, {
        ...init,
        headers,
        signal: controller.signal,
      });
    } catch (error) {
      const reason = error instanceof Error && error.name === 'AbortError' ? '요청 시간이 초과되었습니다.' : '서버에 연결할 수 없습니다.';
      throw new ApiError(`${reason} (${path})`);
    } finally {
      clearTimeout(timer);
    }

    if (!response.ok) {
      throw new ApiError(`요청이 실패했습니다: ${response.status} ${path}`, response.status);
    }

    if (response.status === 204) {
      return undefined as T;
    }
    return (await response.json()) as T;
  }
}

export const jarvisApi = new JarvisApiClient();
export { JarvisApiClient };
