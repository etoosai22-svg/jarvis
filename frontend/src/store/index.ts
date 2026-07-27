import { create } from 'zustand';

import { USE_MOCK_FALLBACK } from '@/config/env';
import { memoryItems as mockMemoryItems, messages as mockMessages, tasks as mockTasks } from '@/data/mockData';
import { jarvisApi } from '@/services/api';
import { toJarvisTask, toMemoryItem, toTaskStatusDto } from '@/services/mappers';
import type { JarvisTask, MemoryItem, Message, TaskState, VoiceState } from '@/types/models';

/** 목업으로 화면을 채운 상태인지 구분해 배너로 알린다. */
export type DataSource = 'live' | 'mock';

type LoadState = {
  loading: boolean;
  error: string | null;
  source: DataSource;
};

const idleLoad: LoadState = { loading: false, error: null, source: 'live' };

let messageSeq = 0;
const nextId = (prefix: string) => `${prefix}-${Date.now().toString(36)}-${(messageSeq += 1)}`;

type AppState = {
  sessionId: string;

  voiceState: VoiceState;
  messages: Message[];
  chat: LoadState;

  tasks: JarvisTask[];
  tasksLoad: LoadState;

  memories: MemoryItem[];
  memoriesLoad: LoadState;

  setVoiceState: (state: VoiceState) => void;
  appendMessage: (message: Message) => void;
  sendMessage: (text: string) => Promise<void>;
  loadTasks: () => Promise<void>;
  setTaskState: (taskId: string, state: TaskState) => Promise<void>;
  loadMemories: (category?: string) => Promise<void>;
};

function describeError(error: unknown): string {
  return error instanceof Error ? error.message : '알 수 없는 오류가 발생했습니다.';
}

export const useAppStore = create<AppState>((set, get) => ({
  sessionId: nextId('session'),

  voiceState: 'idle',
  messages: USE_MOCK_FALLBACK ? mockMessages : [],
  chat: idleLoad,

  tasks: [],
  tasksLoad: { ...idleLoad, loading: true },

  memories: [],
  memoriesLoad: { ...idleLoad, loading: true },

  setVoiceState: (voiceState) => set({ voiceState }),

  appendMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),

  sendMessage: async (text) => {
    const trimmed = text.trim();
    if (!trimmed) return;

    const userMessage: Message = { id: nextId('msg'), role: 'user', content: trimmed };
    set((state) => ({
      messages: [...state.messages, userMessage],
      chat: { loading: true, error: null, source: 'live' },
      voiceState: 'thinking',
    }));

    try {
      const response = await jarvisApi.chat({ session_id: get().sessionId, message: trimmed });
      set((state) => ({
        messages: [...state.messages, { id: nextId('msg'), role: 'assistant', content: response.reply }],
        chat: idleLoad,
        voiceState: 'idle',
      }));

      // 작업 생성·승인 요청·도구 실행이 있었으면 작업 목록을 다시 읽는다.
      const refreshTypes = ['task.created', 'approval.required', 'tool.executed'];
      if (response.actions.some((action) => refreshTypes.includes(action.type as string))) {
        void get().loadTasks();
      }
    } catch (error) {
      set({
        chat: { loading: false, error: describeError(error), source: 'live' },
        voiceState: 'error',
      });
    }
  },

  loadTasks: async () => {
    set((state) => ({ tasksLoad: { ...state.tasksLoad, loading: true, error: null } }));
    try {
      const tasks = (await jarvisApi.listTasks()).map(toJarvisTask);
      set({ tasks, tasksLoad: idleLoad });
    } catch (error) {
      set({
        tasks: USE_MOCK_FALLBACK ? mockTasks : [],
        tasksLoad: {
          loading: false,
          error: describeError(error),
          source: USE_MOCK_FALLBACK ? 'mock' : 'live',
        },
      });
    }
  },

  setTaskState: async (taskId, state) => {
    const previous = get().tasks;
    // 낙관적 갱신 후 실패하면 되돌린다.
    set({ tasks: previous.map((task) => (task.id === taskId ? { ...task, status: state } : task)) });
    try {
      const updated = toJarvisTask(await jarvisApi.updateTaskStatus(taskId, toTaskStatusDto(state)));
      set((current) => ({ tasks: current.tasks.map((task) => (task.id === taskId ? updated : task)) }));
    } catch (error) {
      set((current) => ({
        tasks: previous,
        tasksLoad: { ...current.tasksLoad, error: describeError(error) },
      }));
    }
  },

  loadMemories: async (category) => {
    set((state) => ({ memoriesLoad: { ...state.memoriesLoad, loading: true, error: null } }));
    try {
      const memories = (await jarvisApi.listMemory({ category })).map(toMemoryItem);
      set({ memories, memoriesLoad: idleLoad });
    } catch (error) {
      set({
        memories: USE_MOCK_FALLBACK ? mockMemoryItems : [],
        memoriesLoad: {
          loading: false,
          error: describeError(error),
          source: USE_MOCK_FALLBACK ? 'mock' : 'live',
        },
      });
    }
  },
}));
