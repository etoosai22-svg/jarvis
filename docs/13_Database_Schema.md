# JARVIS Project — Part 13. Database Schema

> **정본 규칙:** 스키마의 정본은 이 문서 + `backend/migrations/`(Alembic)이다.
> 컬럼을 바꾸려면 ① 이 문서 수정 → ② 모델 수정 → ③ `alembic revision --autogenerate` 순서를 지킨다.
> 현재 head: `3bea36f739c5` (create mvp tables)

## 0. 엔진 정책

| 환경 | 엔진 | 스키마 생성 |
|---|---|---|
| 로컬 개발 | SQLite (`sqlite+aiosqlite:///./jarvis.db`) | `AUTO_CREATE_TABLES=true` → 기동 시 `create_all` |
| 컨테이너/운영 | PostgreSQL 15 (`postgresql+asyncpg://…`) | `AUTO_CREATE_TABLES=false` + `alembic upgrade head` |

- 모든 PK는 **String(36) UUID v4** (서버 생성). DB 네이티브 uuid 타입은 SQLite 호환을 위해 쓰지 않는다.
- 모든 시각 컬럼은 **naive UTC** `DateTime`. 값 생성은 반드시 `app/core/time.py:utcnow()` 사용
  (`datetime.utcnow()`·aware datetime 금지 — Postgres `TIMESTAMP`에서 오프셋이 잘린다).
- Redis / Vector DB / Object Storage는 **아직 미사용** — 도입 시점은 §4.

## 1. 테이블 정의 (구현 완료)

### users
| 컬럼 | 타입 | 제약 |
|---|---|---|
| id | String(36) | PK |
| created_at | DateTime | not null, default utcnow |

> 설계상 `name, preferred_name, locale, timezone`은 OAuth 도입(Phase 7)과 함께 추가한다.

### conversations
| 컬럼 | 타입 | 제약 |
|---|---|---|
| id | String(36) | PK |
| user_id | String(36) | nullable, index |
| session_id | String(64) | not null, index |
| started_at | DateTime | not null, default utcnow |
| ended_at | DateTime | nullable — null이면 "열린 대화" |

- **활성 대화 규칙:** `(user_id, session_id, ended_at IS NULL)`인 행이 현재 대화다. chat API는 이 행을 찾거나 만든다.

### messages
| 컬럼 | 타입 | 제약 |
|---|---|---|
| id | String(36) | PK |
| conversation_id | String(36) | nullable, index |
| role | String(32) | not null — `user` 또는 `assistant` |
| content | Text | not null |
| created_at | DateTime | not null, default utcnow |

### tasks
| 컬럼 | 타입 | 제약 |
|---|---|---|
| id | String(36) | PK |
| user_id | String(36) | nullable, index |
| title | String(200) | not null |
| description | Text | nullable |
| status | String(40) | default `queued`, index — 7종 상태는 Part 9 §2 |
| priority | Integer | default 3 (1~5, API 계층에서 검증) |
| payload | Text | nullable — 승인 대기 MCP 호출 JSON `{server,tool,arguments}` (Part 9 승인 실행 규칙) |
| created_at / updated_at | DateTime | not null, default utcnow (updated_at은 onupdate) |
| completed_at | DateTime | nullable — `completed` 상태일 때만 값 존재 |

### memories
| 컬럼 | 타입 | 제약 |
|---|---|---|
| id | String(36) | PK |
| user_id | String(36) | nullable, index |
| category | String(80) | default `general`, index |
| title | String(200) | nullable |
| content | Text | not null |
| embedding_id | String(120) | nullable, index — Vector DB 도입 전 항상 null |
| confidence | Float | default 1.0 (0.0~1.0) |
| tags | Text | nullable — **인코딩 규칙 아래** |
| created_at / updated_at | DateTime | not null, default utcnow |

**tags 인코딩:** 태그 배열을 `\x1f`(unit separator)로 join해 저장한다.
태그 본문에 쉼표가 들어갈 수 있으므로 쉼표 join 금지.
읽기는 하위호환 — `\x1f`가 없으면 쉼표로 split한다 (초기 데이터 호환).

### preferences
| 컬럼 | 타입 | 제약 |
|---|---|---|
| id | String(36) | PK |
| user_id | String(36) | nullable, index |
| key | String(120) | not null, index |
| value | Text | not null |

### audit_logs
| 컬럼 | 타입 | 제약 |
|---|---|---|
| id | String(36) | PK |
| user_id | String(36) | nullable, index |
| action | String(120) | not null |
| target | String(200) | nullable |
| result | Text | not null |
| created_at | DateTime | not null, default utcnow |

## 2. 알려진 부채 (다음 리비전에서 처리)

- `user_id`/`conversation_id`에 **FK 제약 없음** — 격리는 API 계층에서만 보장된다.
  OAuth로 users 행이 실제 생성되기 시작하면 FK + `ON DELETE` 정책을 추가한다.
- `messages.role`, `tasks.status`는 자유 문자열 — CHECK 제약 또는 enum 검토.
- 인덱스는 단일 컬럼뿐 — 대화 조회용 `(user_id, session_id)`, 작업 목록용 `(user_id, created_at)` 복합 인덱스 검토.

## 3. 백업 (운영 전 필수)
PostgreSQL 일일 백업 / 감사 로그 장기 보관 / Object Storage 버전 관리

## 4. 도입 예정 (현재 코드 없음)
| 컴포넌트 | 용도 | 시점 |
|---|---|---|
| Redis | 세션 캐시, 진행 중 작업, 음성 스트리밍 상태, rate limit | Phase 4~ (compose에는 이미 포함) |
| Vector DB | memories 의미 검색 — `embedding_id`가 외부 벡터를 가리키게 됨 | Phase 3 |
| Object Storage | 파일 저장 | Phase 5 (Files MCP) |
