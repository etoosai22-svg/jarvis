# JARVIS Project — Part 9. API Specification

> **이 문서는 계약(contract)이다.** 코드와 이 문서가 다르면 이 문서가 정본이며,
> 동작을 바꾸려면 문서를 먼저 고치고 코드를 맞춘다.
> 기계 판독용 스냅샷: [openapi.json](openapi.json) — 서버 기동 후 `/openapi.json`과 일치해야 한다.

## 0. 기본 규칙

| 항목 | 값 |
|---|---|
| Base URL | `/api/v1` (설정 `API_V1_PREFIX`) |
| 포맷 | JSON (UTF-8). 음성 업로드만 `multipart/form-data` |
| 시간 | 모든 timestamp는 **UTC, 타임존 표기 없는 ISO-8601** (`2026-07-27T00:57:31.191388`). 클라이언트는 `Z`를 붙여 파싱한다 |
| ID | 서버 생성 UUID v4 문자열(36자). 클라이언트는 ID를 만들지 않는다 |
| 인증 | `Authorization: Bearer <JWT>`. §1 참조 |
| 페이지네이션 | 목록 API는 `limit`(기본 50, 최대 200) + `offset`(기본 0) |

### 오류 응답
| 코드 | 의미 | 본문 |
|---|---|---|
| 400 | 도메인 규칙 위반 (예: 잘못된 작업 상태값) | `{"detail": "<사유>"}` |
| 401 | 토큰 없음/무효 (`AUTH_REQUIRED=true`일 때) | `{"detail": "<사유>"}` + `WWW-Authenticate: Bearer` |
| 404 | 리소스 없음 **또는 남의 리소스** (존재 여부를 숨긴다) | `{"detail": "<사유>"}` |
| 422 | 스키마 검증 실패 (FastAPI 기본) | `{"detail": [{loc, msg, type}]}` |

## 1. 인증과 소유권 — 불변식

1. **요청자 식별은 오직 검증된 JWT의 `sub` 클레임에서 온다.**
   요청 본문·쿼리스트링의 `user_id`는 어떤 API에서도 받지 않으며, 보내도 무시된다.
2. 모든 tasks/memory 조회·수정은 요청자 소유 데이터로 자동 스코프된다.
   타인 리소스 접근은 403이 아니라 **404** — 존재 여부 자체를 노출하지 않는다.
3. `AUTH_REQUIRED=false`(로컬 개발)이면 모든 요청이 `DEV_USER_ID`(기본 `local-user`)로 처리된다.
   운영 배포는 반드시 `AUTH_REQUIRED=true` + `OAUTH_ISSUER_URL` 설정.
4. 토큰 검증: JWKS(RS256/ES256), `exp`·`sub` 클레임 필수, `iss`/`aud` 일치 확인.
   (`OAUTH_JWKS_URL` 미설정 시 `{issuer}/.well-known/jwks.json` 사용)
5. `/api/v1/health`만 무인증 공개다.

## 2. 엔드포인트

### GET /api/v1/health — 무인증
```json
{"status": "ok", "service": "JARVIS Backend", "environment": "local"}
```

### POST /api/v1/chat
대화 한 턴을 처리하고 **영속화**한다.

Request:
| 필드 | 타입 | 제약 | 설명 |
|---|---|---|---|
| `session_id` | string | 필수, 1~64자 | 클라이언트 생성 세션 키. 같은 값이면 같은 대화로 이어진다 |
| `message` | string | 필수, 1~12000자 | 사용자 발화 |
| `metadata` | object | 선택, 기본 `{}` | 클라이언트 부가정보 (현재 서버는 무시) |

서버 처리 (순서 보장):
1. `(user, session_id)`의 열린 conversation을 찾거나 생성
2. 직전 대화 `CHAT_HISTORY_LIMIT`(기본 12)턴 + 관련 memory `CHAT_MEMORY_LIMIT`(기본 5)건 회수
3. **오케스트레이터**가 MCP 도구 필요 여부를 판단해 게이트웨이로 호출 (Part 12 규칙 적용)
   - LLM 사용 가능 시: function-calling으로 도구 선택 (최대 6라운드; 한도 도달 시 도구 없이 한 번 더 불러 정리)
   - LLM 없을 때: 규칙 기반 라우터 (날씨/검색/메모/일정 등록)
   - 승인 필수 도구(Part 12 §7)에 걸리면 실행하지 않고 `waiting_for_approval` 작업을 생성
4. user/assistant 메시지 2행을 `messages`에 저장
5. 도구 의도가 없고 작업 키워드(일정·회의·할 일·작업·예약·정리해·보내줘·찾아줘)만 있으면 `queued` 작업 생성

Response:
| 필드 | 타입 | 설명 |
|---|---|---|
| `reply` | string | 어시스턴트 응답 (도구 결과가 반영됨) |
| `task_status` | string | `"waiting_for_approval"` \| `"queued"` \| `"completed"` |
| `actions` | object[] | 부수효과 목록. 타입별 스키마는 아래 |

actions 항목 타입:
| type | 필드 | 의미 |
|---|---|---|
| `task.created` | `task_id, status, source` | 일반 작업 생성 |
| `tool.executed` | `server, tool, status, request_id` | MCP 도구가 실행됨 (status는 Part 12 §5) |
| `approval.required` | `task_id, server, tool` | 승인 대기 작업 생성 — 앱은 승인 카드를 띄우고 아래 PATCH로 응답 |

### GET /api/v1/voice/health — 무인증
활성 음성 제공자 확인: `{"provider": "local"|"openai"|"none", "stt": string|null, "tts": string|null}`

### POST /api/v1/voice
`multipart/form-data`, 필드명 `file` (필수, 빈 파일이면 400, 25MB 초과 413).

**제공자는 `VOICE_PROVIDER`로 고른다** (기본 `auto`). Bedrock 게이트웨이는 음성을 중계하지
않으므로, 키가 없으면 온디바이스(faster-whisper + macOS `say`)로 처리한다.
STT 실패는 예외가 아니라 자리표시 transcript로 떨어진다 — 음성이 안 돼도 대화는 이어져야 한다.

Response: `{"transcript": string, "intent": "task"|"chat", "tts_audio_base64": string|null, "tts_media_type": string|null}`

### GET /api/v1/tasks — 요청자 소유만
Query: `limit`, `offset`. 정렬: `created_at` 내림차순.

TaskRead:
| 필드 | 타입 |
|---|---|
| `id` | string(uuid) |
| `user_id` | string — 항상 요청자 자신 |
| `title` | string(≤200) |
| `description` | string \| null |
| `status` | `queued · planning · waiting_for_approval · running · completed · failed · cancelled` |
| `priority` | int 1~5 |
| `payload` | string(JSON) \| null — 승인 대기 중인 MCP 호출 `{server,tool,arguments}`. 오케스트레이터가 채운다 |
| `created_at` / `completed_at` | timestamp / nullable timestamp |

### POST /api/v1/tasks → 201
Request: `{"title": <1~200자 필수>, "description"?: string, "priority"?: 1~5(기본 3)}`
`status`는 `queued`로 시작. `user_id` 지정 불가(§1).

### PATCH /api/v1/tasks/{task_id}?status_value=<status>
상태 전이. 위 7종 외 값이면 400, 남의/없는 작업이면 404.
`completed`로 바꾸면 `completed_at` 기록, 다른 상태로 바꾸면 `completed_at=null`.

**승인 실행 규칙:** `waiting_for_approval` + `payload` 있는 작업을 `running`으로 전이하면
서버가 그 자리에서 payload의 MCP 호출을 `approved=True`로 실행하고, 결과에 따라
`completed`/`failed`로 마무리해 반환한다 (요청은 도구 타임아웃만큼 걸릴 수 있다 — 최대 30초).
`cancelled`로 전이하면 실행 없이 취소된다. 이것이 앱 승인 카드의 백엔드 계약이다.

### GET /api/v1/memory — 요청자 소유만
Query: `category?`, `limit`, `offset`. 정렬: `updated_at` 내림차순.

MemoryRead:
| 필드 | 타입 |
|---|---|
| `id` | string(uuid) |
| `user_id` | string — 항상 요청자 자신 |
| `category` | string(≤80), 기본 `general` |
| `title` | string(≤200) \| null |
| `content` | string |
| `embedding_id` | string \| null — 벡터 검색 도입 전까지 항상 null |
| `confidence` | float 0.0~1.0 |
| `tags` | string[] — 태그에 쉼표 포함 가능 (저장 형식은 Part 13) |
| `created_at` / `updated_at` | timestamp |

### POST /api/v1/memory → 201
Request: `{"content": <필수>, "category"?, "title"?, "confidence"?: 0~1, "tags"?: string[]}`

### POST /api/v1/memory/search
Request: `{"query": <필수 1자+>, "limit"?: 1~50(기본 10)}`
현재 구현: `content`/`title` ILIKE 부분일치, `updated_at` 내림차순.
(벡터 검색은 Phase 3 — 도입 후에도 이 요청/응답 계약은 유지한다)

## 3. WebSocket — `WS /api/v1/ws/voice`

JSON 이벤트를 최상위 필드로 주고받는다 (payload 래핑 없음).

Client → Server:
| type | 필드 | 설명 |
|---|---|---|
| `session.start` | `session_id` | 연결 직후 1회 |
| `audio.chunk` | `audio`(base64) | 스트리밍 청크 |
| `audio.end` | — | 발화 종료 |
| `task.cancel` | — | 진행 작업 취소 |
| `approval.respond` | `approved`(bool) | 승인 응답 |

Server → Client: `task.started{session_id}`, `transcript.partial{text,chunk_count}`, `transcript.final{text}`, `assistant.delta{text}`, `audio.output{format,text}`, `task.progress{status}`, `task.completed{status}`, `error{message}`

**`audio.end` 수신 시 서버가 도는 순서:** 누적 청크 → STT → `transcript.final` →
`POST /chat`과 **동일한 오케스트레이터**(도구 선택·승인 정책) → **문장 단위 스트리밍**.

**`assistant.delta`와 `audio.output`은 한 턴에 여러 번 나간다.** LLM 응답을
문장이 완성되는 대로 흘려보내므로 첫 소리까지의 시간이 응답 전체 길이와 무관해진다.
클라이언트는 델타를 **같은 말풍선에 이어붙이고**, 오디오는 **도착 순서대로 큐에 넣어**
재생해야 한다 (겹쳐 재생하면 문장이 뒤섞인다).

`task.progress` / `approval.required`는 **도구가 실행된 즉시** 나간다 — 응답보다 먼저다.
도구는 응답 생성 전에 실행되며, 순서를 뒤집으면 앱 음성 상태가
"답변 중"에서 "실행 중"으로 되돌아간다.

`audio.output`은 두 형태다: TTS 성공 시 `{format:"base64", media_type, audio}`,
실패·비활성 시 `{format:"text", text}`. 오디오는 프레임 한도(1MB)를 넘지 않도록 압축해서 보낸다.

**음성 응답 길이:** 음성 경로는 시스템 프롬프트에 "2~3문장, 마크다운 금지" 지침을 덧붙인다.
출력 토큰이 지연을 지배하므로(초당 약 60토큰) 길이 제한이 곧 체감 속도다.

> **현재 상태:** 발화 단위 처리는 완료(파일 업로드·WS 모두 실제 STT/LLM/TTS를 탄다).
> 스트리밍 부분 인식(말하는 중 실시간 transcript)은 아직 자리표시이며,
> WS 인증은 Phase 7 대상이다.

## 4. 명시적으로 없는 것 (향후 계약 추가 대상)
- DELETE (tasks/memory), memory 수정(PUT/PATCH)
- Streaming chat response, Push Notification, Multi-device sync
- Rate limit (Redis 도입 시 `429` + `Retry-After` 추가 예정)
