# JARVIS Project
## Part 9. API Specification

### Architecture
iPhone App → REST/WebSocket → JARVIS API → Orchestrator → MCP Gateway → External Services

### 주요 API

#### POST /api/v1/chat
사용자 음성 또는 텍스트 요청 전달
- Request: session_id, message, metadata
- Response: reply, task_status, actions

#### POST /api/v1/voice
음성 업로드
- Response: transcript, intent

#### GET /api/v1/tasks
현재 작업 조회

#### GET /api/v1/memory
사용자 기억 조회

#### POST /api/v1/memory
사용자 선호 저장

### 공통 원칙
- JSON 사용
- HTTPS 필수
- OAuth 인증
- UUID 기반 Session 관리

### 오류 코드
- 200 Success
- 400 Bad Request
- 401 Unauthorized
- 404 Not Found
- 500 Internal Error

### 향후 계획
- Streaming Response
- Real-time Voice
- Multi-device Sync
- Push Notification API
