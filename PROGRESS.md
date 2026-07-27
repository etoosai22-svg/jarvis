# JARVIS Progress

## 2026-07-27 (7) — 응답 지연 실측·개선 (첫 소리 14.5초 → 7.9초)

Slack 대화가 5초씩 걸린다는 지적에서 출발해 파이프라인 단계별로 실측:

| 단계 | 실측 |
|---|---|
| STT (웜) | 0.31초 |
| MCP 도구 스키마 22개 수집 | 0.01초 |
| LLM 도구 선택 (입력 4,102토큰) | 2.1초 |
| LLM 응답 생성 | 84토큰 2.7초 / 400토큰 6.6초 (**초당 ~60토큰**) |
| TTS (문장 길이 무관) | 1.1초 |

**병목은 출력 토큰 하나** — 입력은 4천 토큰을 넣어도 2초다. 개선 세 가지:

- **① 음성 응답 길이 제한**: 음성 경로에만 "2~3문장, 마크다운 금지" 지침 추가
- **② 문장 단위 스트리밍**: 게이트웨이가 SSE를 지원하는 걸 확인하고
  (`stream: true`, 첫 토큰 2.0초), 문장이 완성될 때마다 TTS→전송.
  클라이언트는 델타를 같은 말풍선에 이어붙이고 오디오를 큐로 순서 재생
- **③ 도구 왕복 제거**: 아래 결함 참조

발견한 결함 2건:
- **Open-Meteo 지오코딩이 "서울"을 못 찾는다** (0건, "Seoul"은 정상 / "부산"은 성공).
  모델이 한국어로 부르면 실패하고 영어로 재시도 → **LLM 라운드 하나를 통째로 낭비**(약 4.5초).
  주요 도시 영문 별칭 폴백 + 좌표 캐시 추가
- **스트리밍 경로에서 도구 이벤트가 통째로 유실**. 액션을 `handle_chat` 반환값에서 읽었는데
  콜백은 그 전에 실행된다 → `on_action` 콜백으로 발생 즉시 통지하도록 변경

실측 결과: 첫 소리 14.5초 → 10.9초(도구 왕복 제거) → **7.9초**(좌표 캐시 적중).
테스트 백엔드 45 + MCP 37.

**남은 지연**: LLM 도구 선택 ~4초, 날씨 API 왕복 ~2초, TTS 1초.
2초대로 가려면 도구 선택을 Haiku로 라우팅하거나 도구 없는 대화를 1라운드로 줄여야 한다.


## 2026-07-27 (6) — 앱 음성 입출력 연결

- `expo-audio` + `expo-file-system` 추가. 16kHz 모노로 녹음 (whisper 입력 규격,
  전송량도 44.1kHz 스테레오 대비 훨씬 작다)
- `useVoiceCapture` 훅이 마이크를 소유하고, 전송 이후는 스토어가 맡는다 —
  화면은 `voiceState` 하나만 본다. 오브·마이크 버튼 모두 같은 토글에 물렸다
- **WS 프로토콜을 네이티브 의존에서 분리**: `voiceSession.ts`(프로토콜, expo 무의존) /
  `voiceAudio.ts`(녹음 읽기·재생·권한). 덕분에 브라우저에서 실제 경로를 그대로 검증했다
- iOS `NSMicrophoneUsageDescription` + Android `RECORD_AUDIO` 설정
- **결함**: 서버가 `assistant.delta`를 액션 이벤트보다 먼저 보내서 오브가
  "답변 중" → "실행 중"으로 **되돌아갔다**. 도구는 응답 생성 전에 실행되므로
  이벤트도 그 순서로 보내도록 백엔드 수정 (docs/09 §3에 명시)
- 실검증: 녹음본을 스토어에 주입해 전 구간 재생 —
  `transcribing → thinking → executing → speaking → idle`,
  대화 화면에 사용자 발화와 실제 날씨 응답이 렌더링됨


## 2026-07-27 (5) — LLM을 Bedrock으로, Phase 4 음성 대화 루프 완성

### LLM: openclaw Bedrock 게이트웨이
- 게이트웨이가 OpenAI completions 규약을 말해서 **SDK 교체 없이 base_url만** 바꾸면 됐다
- 설정을 공급자 중립으로 (`LLM_API_KEY`/`LLM_BASE_URL`/`LLM_CHAT_MODEL`), `build_client()` 팩토리로 통합
- **결함 ①** 두 호출부가 `temperature=0.4`를 하드코딩 → Bedrock이 502로 거부
  (`temperature`는 Claude Opus 4.7/Sonnet 5에서 API에서 제거됨). chat·오케스트레이터가
  조용히 규칙 라우터로 폴백하고 있었다. 기본 미전송으로 변경
- **결함 ②** `.env` 추가 후 테스트가 실제 Bedrock을 호출 (스위트 0.7초 → 133초).
  conftest에서 LLM/음성 공급자를 명시적으로 차단

### Phase 4: 음성
- 제공자 추상화 `app/services/voice/` — local(faster-whisper + macOS `say`) / openai / none
- Bedrock 게이트웨이는 채팅만 중계하므로 **기본은 온디바이스** (키 불필요, 오디오가 기기를 안 떠남)
- **WS가 자리표시 문구 대신 실제 파이프라인을 돈다**: STT → 오케스트레이터(도구·승인) → TTS
- **결함 ③** `send(..., **action)`이 `status`/`type`과 충돌해 TypeError → WS 종료
- **결함 ④** 무압축 AIFF가 WS 1MB 프레임 한도 초과 → ffmpeg AAC 압축 (1.7MB → 39KB)
- **결함 ⑤** 도구 라운드 한도(3)에 걸리면 "한도에 도달했습니다"를 **음성으로 읽어줬다**.
  한도 6으로 올리고, 걸려도 도구 없이 한 번 더 불러 정리하도록 변경
- 실검증: 음성 왕복 2회 — 날씨(즉시 실행, 14초) / 일정(승인 요청, 23초) 전 구간 통과
- 테스트 39개


## 2026-07-27 (4) — 실동작 검증에서 결함 4건 발견·수정

실키(OpenAI)와 Xcode가 이 머신에 없어, 가능한 최대치로 검증하고 막힌 곳은 명시:

- **LLM 경로**: OpenAI SDK 타입 그대로 쓰는 모킹 테스트 5개 추가 (도구 22개 스키마 유효성,
  tool_call → 게이트웨이 → tool 메시지 회신, 승인 분기, 라운드 한도, 장애 시 규칙 라우터 폴백)
  → **결함 ①** `Settings(openai_api_key=...)`가 조용히 무시됨 (validation_alias + populate_by_name 부재)
- **승인 루프 라이브 HTTP**: 실서버로 chat → 승인 → 취소 왕복
  → **결함 ②** 승인 *요청*과 *거절*이 감사 로그에 안 남음 (실행된 것만 기록) → `record_decision` 추가
- **앱 UI**: Xcode 미설치로 시뮬레이터 불가 → Expo 웹으로 검증
  → **결함 ③** nativewind가 `react-native-worklets` 부재로 번들 자체를 깨뜨림 (웹·네이티브 공통).
    실사용은 className 1곳뿐이라 제거 → 번들 성공
  → **결함 ④** Tasks 화면 승인/취소 버튼에 onPress 미연결 (죽은 버튼) → 연결 후 재검증:
    앱 클릭 → MCP 캘린더에 이벤트 생성 + 감사 2건 확인
- 테스트: 백엔드 38 + MCP 34 = 72개

## 2026-07-27 (3) — 오케스트레이터: chat → 도구 호출 → 승인 루프

- `app/services/orchestrator.py`: LLM function-calling(키 있을 때, 최대 3라운드) +
  규칙 라우터(키 없을 때: 날씨/검색/메모/일정 등록, '내일 10시' 시각 파서 포함)
- 승인 루프 완성: 승인 필수 도구 → `waiting_for_approval` 작업(payload에 보류 호출 저장)
  → 앱 승인 카드 → `PATCH running` 시 approved=True로 실행 → completed/failed
  → 취소 시 실행 안 됨 (E2E 테스트로 캘린더 실제 생성/미생성 확인)
- 계약 선행 수정: docs/09 actions 타입 표·승인 실행 규칙, docs/13 tasks.payload
  (+Alembic `b99dad96a5f1`)
- 테스트 32개(오케스트레이터 9 신규) + MCP 34 = 66개, tsc 무오류

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
