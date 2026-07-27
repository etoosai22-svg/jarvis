# JARVIS Project — Part 18. Testing Strategy

> **원칙:** 수용 기준은 "무엇을 테스트한다"가 아니라 **통과/실패를 판정할 수 있는 문장**으로 쓴다.
> 구현자가 자기 코드에 테스트를 붙이는 것이 아니라, 이 문서의 기준에서 테스트를 먼저 뽑는다.

## 0. 현재 상태 (2026-07-27)

| 스위트 | 위치 | 상태 |
|---|---|---|
| Backend API | `backend/tests/` — 16 tests | ✅ 통과 (`uv run --extra test python -m pytest -q`) |
| Frontend 타입 | `frontend/` | ✅ `npx tsc --noEmit` 무오류 |
| CI | `.github/workflows/ci.yml` | ✅ main push/PR 시 backend·frontend 잡 자동 실행 |
| E2E / 음성 / 성능 | — | ❌ 미작성 |

테스트 DB는 임시 파일 SQLite(`tests/conftest.py`)를 쓴다 — 개발용 `jarvis.db`를 오염시키지 않는다.

## 1. 수용 기준 (Phase 2 — 전부 테스트로 존재해야 함)

### 인증·소유권 (Part 9 §1의 불변식과 1:1 대응)
- [x] `AUTH_REQUIRED=true` + 토큰 없음 → 보호 라우트 전부 **401** (`test_auth.py`)
- [x] `AUTH_REQUIRED=true` + 위조 토큰 → **401** (`test_auth.py`)
- [x] `/api/v1/health`는 인증 켜도 **200** (`test_auth.py`)
- [x] 요청 본문의 `user_id`는 무시되고 인증 주체로 저장 (`test_api.py`)
- [ ] 사용자 A 토큰으로 B의 task PATCH → **404** (두 사용자 토큰 발급이 가능해지는 OAuth 도입 시)

### 대화 영속화
- [x] chat 1턴 → user/assistant 메시지 2행 저장, 같은 `session_id` 재호출 시 conversation 재사용
- [x] 작업 키워드 포함 발화 → `actions[0].type == "task.created"` + 해당 task가 GET /tasks에 노출
- [x] 키워드 없는 발화 → `task_status == "completed"`, `actions == []`
- [x] OpenAI 키 없음 → 500이 아니라 fallback 응답 (테스트는 키 없이 돈다)

### 데이터 규칙
- [x] 태그에 쉼표 포함 (`"회의, 자료"`) → 왕복 후 원형 보존
- [x] 잘못된 작업 상태값 → **400**, 없는 task → **404**
- [x] `completed` 전이 시 `completed_at` 기록

### WebSocket
- [x] `session.start → audio.chunk → audio.end` 시퀀스가 계약된 이벤트 순서로 응답

### 마이그레이션
- [x] `alembic upgrade head` → 7개 테이블 생성, `downgrade base` 왕복 무오류 (수동 검증 — CI 편입 대상)

## 2. 자동화 — 구현됨 (`.github/workflows/ci.yml`)

main에 대한 push/PR에서 두 잡이 병렬 실행된다:
1. **backend**: `uv sync --extra test` → `pytest -q` → `alembic upgrade head` + `downgrade base` 왕복
2. **frontend**: `npm ci` → `npx tsc --noEmit`

병합 조건: 두 잡 모두 green.

남은 항목:
- [ ] GitHub 저장소 설정에서 main 브랜치 보호 규칙에 두 잡을 required check으로 등록
- [ ] Lint (ruff / biome) 잡 추가
- [ ] 커버리지 측정 — 목표 수치(90%)는 측정이 시작된 뒤에 관리한다

## 3. Phase별 추가 예정
- **Phase 3 (메모리)**: 벡터 검색 정확도 스냅숏, memory 회수 상위 k 검증
- **Phase 4 (음성)**: STT mock 기반 Voice Flow — 음성 입력 → intent → 응답 이벤트 순서
- **Phase 5 (MCP)**: Mock MCP 서버로 도구 호출 봉투·타임아웃·승인 정책(Part 12 §7) 검증
- **성능**: 일반 API p95 < 1초, 첫 음성 응답 < 2초 — 측정 스크립트부터 작성
