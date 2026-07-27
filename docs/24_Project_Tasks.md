# JARVIS Project — Part 24. Project Development Tasks

> **상태 기준일: 2026-07-27.** 체크는 "코드가 저장소에 있고 검증됨"을 뜻한다.
> ◐ = 부분 완료 (부족한 부분을 항목 옆에 명시).

## Phase 1 - 프로젝트 기반
### 저장소
- [x] Git 저장소 생성 (`~/JARVIS`, GitHub `etoosai22-svg/jarvis`)
- [ ] 브랜치 전략 정의 (현재 main 단일 브랜치)
- [x] README 작성  - [ ] LICENSE 추가  - [x] .gitignore 구성

### 개발 환경
- [x] Docker 구성 (backend/Dockerfile — 루트 컨텍스트, 기동 시 alembic)
- [x] Docker Compose 구성 (api + postgres(healthcheck) + redis)
- [x] Python 환경 구성 (uv + pyproject)  - [x] React Native 초기화 (Expo 53)
- [x] 환경변수 관리 (.env.example, EXPO_PUBLIC_*)

### CI/CD
- [x] GitHub Actions (`.github/workflows/ci.yml` — backend·frontend 잡)
- [ ] Lint (ruff/biome 잡 미추가)  - [x] Unit Test 자동 실행  - [ ] Build 자동화
> 브랜치 보호 규칙 등록은 미완. 기준은 Part 18 §2.

## Phase 2 - Backend
### API
- [x] FastAPI 초기화
- [◐] 인증 API — JWT 검증·소유권 스코프 완료 / IdP 연동·토큰 발급은 Phase 7
- [x] Chat API (영속화 + 메모리 회수 + 시스템 프롬프트)
- [x] Memory API  - [x] Task API

### Database
- [◐] PostgreSQL 연결 — asyncpg·compose 준비 완료 / 실 Postgres 대상 검증 미실시
- [x] Alembic 설정 (head: 3bea36f739c5, up/down 왕복 검증)
- [x] users / conversations / messages / tasks / memories 테이블 (+preferences, audit_logs)

### Redis
- [ ] 세션 저장  - [ ] 캐시  - [ ] Rate Limit (컨테이너만 떠 있음, 코드 미사용)

## Phase 3 - Frontend
- [◐] Home 화면 — UI 완료, 일정·최근대화가 아직 목업
- [x] Conversation 화면 (실 채팅 전송, 승인/취소 동작)
- [x] Task 화면 (실데이터, 세그먼트 필터, 새로고침)
- [x] Memory 화면 (실데이터, 카테고리 필터)
- [◐] Settings 화면 — UI만, 연동 서비스 상태가 목업
- 공통: 백엔드 미가동 시 목업 폴백 + 경고 배너, `tsc --noEmit` 무오류

## Phase 4 - Voice
- [◐] STT 연동 — 업로드형(POST /voice)만, 앱에서 녹음·전송 미구현
- [◐] TTS 연동 — 서버 합성만, 앱 재생 미구현
- [ ] 실시간 스트리밍 (WS 이벤트 계약만 존재, transcript는 자리표시)
- [x] 음성 상태 UI (VoiceOrb 7종 상태)

## Phase 5 - MCP — 전체 미착수
- [ ] Search  - [ ] Calendar  - [ ] Notes  - [ ] Files  - [ ] Weather  - [ ] Booking(2차)
> 명세는 Part 12에 구현 가능 수준으로 존재. `mcp/` 디렉터리는 빈 스캐폴드.

## Phase 6 - AI
- [x] System Prompt (`prompts/system_prompt.md` — 서버가 실제 로드)
- [◐] Memory Retrieval — 키워드 ILIKE. 벡터 검색으로 교체 예정
- [ ] Planner  - [ ] Tool Selection  - [ ] Response Generator

## Phase 7 - Security
- [◐] OAuth — 서버측 검증 완료(S1~S4), IdP·로그인 플로우 미착수
- [ ] HTTPS  - [ ] Secret Manager  - [ ] Audit Log 기록 코드

## Phase 8 - Testing
- [x] Unit/API Test (16개, 수용 기준은 Part 18 §1)
- [ ] Integration Test (실 Postgres)  - [ ] Voice Test  - [ ] E2E Test  - [ ] Performance Test

## Phase 9 - Release
- [ ] Alpha  - [ ] Beta  - [ ] v1.0
