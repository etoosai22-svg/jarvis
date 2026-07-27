import type { Integration, JarvisTask, MemoryItem, Message } from '@/types/models';

export const todaySchedules = [
  { time: '10:00', title: '전략 회의', meta: '회의실 A · 30분 전 알림' },
  { time: '15:00', title: '팀 미팅', meta: 'Google Calendar 연결됨' },
  { time: '18:30', title: '저녁 약속', meta: '강남역 · 이동 35분' },
];

export const recentConversations = [
  { icon: '💬', title: '내일 회의 시간 알려줘', meta: '2분 전' },
  { icon: '☁️', title: '서울 날씨 어때?', meta: '어제' },
  { icon: '📝', title: '회의록 정리해줘', meta: '금요일' },
];

export const messages: Message[] = [
  { id: 'm1', role: 'assistant', content: '네, 실장님. 오전 10시 전략 회의와 오후 3시 팀 미팅이 있습니다.' },
  { id: 'm2', role: 'user', content: '회의 준비 해줘' },
  { id: 'm3', role: 'assistant', content: '관련 자료 3건을 찾았습니다. 핵심 쟁점을 요약 중입니다', streaming: true },
];

export const tasks: JarvisTask[] = [
  { id: 't1', title: '회의 준비 자료 검색', subtitle: '자료를 찾고 요약하고 있습니다.', status: 'running', progress: 64, service: 'Google Search' },
  { id: 't2', title: '이메일 초안 발송', subtitle: '실행 전 확인이 필요합니다.', status: 'approval_required', progress: 38, service: 'Gmail' },
  { id: 't3', title: '오늘 날씨 조회', subtitle: '완료 — 대화에서 결과를 확인하세요.', status: 'completed', progress: 100, service: 'Weather MCP' },
  { id: 't4', title: 'Notion 페이지 업데이트', subtitle: '재인증 후 다시 시도할 수 있어요.', status: 'failed', service: 'Notion' },
];

export const memoryItems: MemoryItem[] = [
  { id: 's1', title: '“회의 전 자료 요약을 선호”', content: '새 기억으로 저장할까요?', source: '대화에서 감지', suggested: true },
  { id: 'm1', title: '커피: 아이스 아메리카노', content: '카페 주문 요청 시 기본값으로 사용합니다.', source: '대화에서 저장 · 3일 전' },
  { id: 'm2', title: '호칭: 실장님', content: '응답 시작 문구에 반영합니다.', source: '설정에서 저장' },
];

export const integrations: Integration[] = [
  { id: 'calendar', title: 'Google Calendar', subtitle: '일정 조회·추가 가능', status: 'connected' },
  { id: 'gmail', title: 'Gmail', subtitle: '권한 갱신 필요', status: 'expired' },
  { id: 'notion', title: 'Notion', subtitle: '워크스페이스 연결 필요', status: 'disconnected' },
  { id: 'weather', title: 'Weather', subtitle: '현재 서비스 오류', status: 'error' },
];
