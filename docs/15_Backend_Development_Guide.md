# JARVIS Project
## Part 15. Backend Development Guide

### 기술 스택
Python 3.12+ / FastAPI / Pydantic / SQLAlchemy + Alembic
PostgreSQL / Redis / WebSocket / Celery or Arq / Docker / OpenTelemetry + Sentry

### 프로젝트 구조
```
backend/
├── app/
│   ├── main.py
│   ├── api/
│   ├── core/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   ├── mcp/
│   ├── repositories/
│   └── workers/
├── tests/
├── migrations/
├── Dockerfile
└── pyproject.toml
```

### 핵심 서비스
- **API Service**: REST API, WebSocket, 인증, 요청 검증
- **Orchestrator Service**: 의도 분석 → 작업 분해 → MCP 도구 선택 → 결과 통합
- **Memory Service**: 단기 컨텍스트, 장기 기억 검색, 사용자 선호 반영
- **Task Service**: 작업 생성, 상태 변경, 진행률 관리
- **Approval Service**: 승인 필요 작업 분류 및 처리

### 오케스트레이터 흐름
```
Request → Intent Classification → Context & Memory Retrieval
→ Plan Generation → Risk/Approval Check → MCP Tool Execution
→ Result Validation → Response Synthesis → Memory Update
```

### 작업 상태
queued / planning / waiting_for_approval / running / completed / failed / cancelled

### WebSocket 이벤트
client → server: session.start, audio.chunk, audio.end, task.cancel, approval.respond
server → client: transcript.partial, transcript.final, assistant.delta, task.started, task.progress, task.completed, approval.required, audio.output, error

### Redis 사용
세션 / WebSocket 연결 상태 / 작업 진행률 / 분산 락 / Rate Limit / 단기 대화 컨텍스트

### 보안
- OAuth 2.0 / OpenID Connect
- Access Token 단기 사용 / Refresh Token 안전 저장
- 사용자별 데이터 격리
- 민감 작업 재인증 지원
- 비밀키 Git/로그 저장 금지

### 계층 원칙
- Route: 입출력 + 권한 검증만
- Service: 비즈니스 로직
- Repository: 데이터 접근
- MCP Client/Adapter: 외부 연동
