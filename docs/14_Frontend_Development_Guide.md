# JARVIS Project
## Part 14. Frontend Development Guide

### 기술 스택
React Native / TypeScript / Expo or React Native CLI
React Navigation / Zustand or Redux Toolkit / TanStack Query
WebSocket / Secure Storage / Native Audio APIs / Sentry

### 앱 구조
```
src/
├── app/          (navigation, providers, config)
├── screens/      (Home, Conversation, Tasks, Memory, Settings)
├── components/   (VoiceButton, Waveform, MessageBubble, TaskStatusCard)
├── features/     (voice, chat, tasks, memory, auth)
├── services/     (api, websocket, audio, storage)
├── hooks/
├── store/
├── types/
└── utils/
```

### 핵심 화면
- **Home**: 중앙 음성 호출 버튼, 오늘 브리핑, 진행 작업, 최근 대화
- **Conversation**: 실시간 음성 파형, 사용자/AI 대화, 작업 진행 상태
- **Tasks**: 진행 중 / 완료 / 승인 대기 / 실패
- **Memory**: 사용자 선호, 저장된 기억, 수정 및 삭제
- **Settings**: 계정, 음성, 알림, MCP 연결 상태

### 음성 인터페이스 상태
```
idle → listening → transcribing → thinking → executing → speaking → error
```
각 상태는 화면과 음성 피드백에 명확히 반영

### WebSocket 이벤트
client → server: session.start, audio.chunk, audio.end, task.cancel, approval.respond
server → client: transcript.partial, transcript.final, assistant.delta, task.started, task.progress, task.completed, approval.required, audio.output, error

### 컴포넌트 원칙
- 모든 컴포넌트 TypeScript 사용
- 비즈니스 로직과 UI 분리
- 로딩 / 빈 상태 / 오류 상태 제공
- 접근성 라벨 필수
- 네트워크 실패 시 재시도 지원

### UX 원칙
음성 중심 / 최소한의 터치 / 한 손 조작 / 3초 내 응답 시작
