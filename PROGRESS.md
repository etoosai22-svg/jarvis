# JARVIS Progress

## 2026-07-26 15:42 KST — FastAPI Backend MVP 구현 완료

- 작업 디렉터리: `/Users/etoos/JARVIS/backend`
- 참조 문서:
  - `/Users/etoos/.openclaw/workspace-cos/JARVIS/docs/09_API_Spec.md`
  - `/Users/etoos/.openclaw/workspace-cos/JARVIS/docs/13_Database_Schema.md`
  - `/Users/etoos/.openclaw/workspace-cos/JARVIS/docs/15_Backend_Development_Guide.md`

### 구현 산출물

- `pyproject.toml`: FastAPI, SQLAlchemy async, Redis, OpenAI, websockets, pytest 계열 의존성 정의
- `app/main.py`: FastAPI 앱, CORS, lifespan DB 초기화, `/health`, `/api/v1/health`
- `app/core/config.py`: Pydantic Settings 기반 환경설정
- `app/core/database.py`: SQLAlchemy async engine/session/init_db
- `app/api/v1/endpoints/chat.py`: `POST /api/v1/chat`
- `app/api/v1/endpoints/voice.py`: `POST /api/v1/voice`, `WS /api/v1/ws/voice`
- `app/api/v1/endpoints/tasks.py`: 작업 CRUD 기본 라우터
- `app/api/v1/endpoints/memory.py`: 메모리 생성/조회/검색 라우터
- `app/models/*`: users, conversations, messages, tasks, memories, preferences, audit_logs MVP 테이블 모델
- `docker-compose.yml`: api + postgres + redis 구성
- `.env.example`: 로컬/컨테이너 실행 환경 변수 예시
- `Dockerfile`: compose api 빌드용 컨테이너 정의
- `tests/test_api.py`, `tests/test_health.py`: API/WS 스모크 테스트

### 검증 결과

- `uv run --extra test python -m pytest -q` → 6 passed, 5 warnings
- `uv run python -m compileall app -q` → 통과
- `docker compose config`는 현재 호스트에 Docker CLI가 없어 실행 불가 (`docker: command not found`)
- 대신 `docker-compose.yml` 필수 키(`services`, `api`, `postgres`, `redis`, `volumes`) 정적 확인 완료

### 남은 주의사항

- OAuth/OIDC 인증은 설정 필드만 준비된 상태이며 실제 토큰 검증 미구현
- OpenAI 키가 없으면 chat/voice는 fallback 응답으로 동작
- Repository 계층은 아직 분리하지 않은 MVP 구조
