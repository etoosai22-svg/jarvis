# JARVIS Progress

## 2026-07-27 (2) — Phase 5: MCP 서버 5종 + 게이트웨이

- 진행 방식: 공통 규약(`mcp/src/jarvis_mcp/__init__.py`) + 본보기(weather) 고정 후
  search/calendar/notes/files 4종을 병렬 에이전트로 구현 — 공유 파일 충돌 0건
- 게이트웨이(`backend/app/services/mcp_gateway.py`): Part 12 §4 봉투, §7 승인 정책
  (calendar 변이 도구는 approved=True 필수), §8 재시도, §9 타임아웃, §11 감사 로그
- 검증: MCP 34 + 게이트웨이 7 + 기존 16 = 테스트 57개, CI 3잡(backend/mcp/frontend) green
- 다음: 오케스트레이터 — chat이 도구를 선택·호출하고 승인 플로우를 앱 WS로 노출

## 2026-07-27 — 저장소 정리 + 앱/백엔드 연결

### 1. 버전 관리
- `/Users/etoos/JARVIS`를 git 저장소로 초기화 (그 전까지 백업 없이 로컬에만 존재)
- `.gitignore`: `.venv`, `node_modules`, `*.db`, `.env`, `.expo` 제외

### 2. 프론트엔드 ↔ 백엔드 연결
- `src/config/env.ts`: `EXPO_PUBLIC_API_BASE_URL` 기반 API/WS 주소
- `src/types/api.ts`: 백엔드 DTO 및 `WS /api/v1/ws/voice` 이벤트 타입
- `src/services/api.ts`: 타임아웃·Bearer 토큰 훅·음성 WebSocket을 갖춘 API 클라이언트
- `src/services/mappers.ts`: DTO ↔ 화면 모델 변환 (작업 상태 7종 → 6종)
- `src/store/index.ts`: zustand 스토어 (대화/작업/메모리 + 목업 폴백)
- Tasks/Memory/Conversation 화면을 실데이터로 전환, 백엔드 미가동 시 배너 노출
- `npx tsc --noEmit` 통과

### 3. 백엔드 보안·대화 영속화
- `app/core/security.py`: JWKS 기반 JWT 검증 + `AUTH_REQUIRED=false` 로컬 우회
- 작업/메모리 조회를 인증 주체로 스코프 (요청 본문의 `user_id` 무시)
- `app/services/chat_service.py`: conversation/message 영속화, 메모리 회수,
  `prompts/system_prompt.md` 기반 시스템 프롬프트, 작업 자동 생성
- `datetime.utcnow()` → `app/core/time.py:utcnow()` (deprecation 경고 제거)
- 메모리 태그 구분자를 쉼표 → `\x1f` (태그 안 쉼표 보존, 기존 데이터 호환)

### 4. 마이그레이션 / 실행 환경
- Alembic 초기화 + `create mvp tables` 리비전, upgrade/downgrade 왕복 검증
- `AUTO_CREATE_TABLES` 설정 추가 (SQLite 로컬 편의용, Postgres에서는 Alembic)
- Dockerfile 빌드 컨텍스트를 저장소 루트로 변경 (`prompts/` 포함), 기동 시 `alembic upgrade head`
- docker-compose에 postgres healthcheck 추가

### 검증 결과
- `uv run --extra test python -m pytest -q` → **16 passed**
- `npx tsc --noEmit` → 오류 없음
- 실제 서버 기동 후 chat 2회 → messages 4행 + conversation 1행 재사용 확인,
  chat이 만든 작업이 `/api/v1/tasks`에 노출되는 것까지 확인

### 남은 작업
- `.github/workflows` CI 비어 있음 (lint/test 자동화 미구성)
- `mcp/{search,calendar,notes,files,weather}` 전부 빈 디렉터리 — Phase 5 미착수
- Redis(세션/캐시/rate limit) 미사용, 음성 WebSocket은 아직 하드코딩 응답
- 벡터 검색 없음 — 메모리 회수는 키워드 ilike 기반

---

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
