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
- [◐] Home 화면 — 음성 오브가 실제로 녹음·전송한다. 일정·최근대화는 아직 목업
- [x] Conversation 화면 (실 채팅 전송, 승인/취소 동작)
- [x] Task 화면 (실데이터, 세그먼트 필터, 새로고침)
- [x] Memory 화면 (실데이터, 카테고리 필터)
- [◐] Settings 화면 — UI만, 연동 서비스 상태가 목업
- 공통: 백엔드 미가동 시 목업 폴백 + 경고 배너, `tsc --noEmit` 무오류

## Phase 4 - Voice
- [x] STT 연동 — 제공자 추상화(local/openai). 기본은 온디바이스 faster-whisper
- [x] TTS 연동 — macOS `say`(한국어) + ffmpeg AAC 압축, OpenAI TTS도 지원
- [x] **음성 대화 루프** — WS가 실제 파이프라인을 돈다: STT → 오케스트레이터(도구·승인) → TTS
- [◐] 실시간 스트리밍 — **응답은 문장 단위 스트리밍**. 첫 소리 14.5초 →
  대화 턴 2.4초 / 도구 턴 2.5~5.3초. 말하는 중 부분 인식(입력 스트리밍)은 여전히 자리표시
- [x] 음성 상태 UI (VoiceOrb 7종 상태)
- [x] 앱에서 녹음·전송·재생 — expo-audio 16kHz 모노 녹음 → WS 전송 → TTS 재생.
  오브/마이크 버튼 토글, 마이크 권한 거부 시 안내 배너 (iOS·Android 권한 문구 설정 완료)

## Phase 5 - MCP
- [◐] Search — search_web/news/open_result/extract_summary (products/tickets는 2차)
- [◐] Calendar — 도구 5종 완료, 로컬 sqlite 스토어 (Google 연동 시 내부 교체)
- [◐] Notes — 도구 4종 완료, 로컬 sqlite 스토어
- [x] Files — 도구 5종 + 샌드박스 탈출 차단 (상대·절대·심링크 3경로 테스트)
- [◐] Weather — Open-Meteo 4종 (특보는 제공자 부재로 빈 목록)
- [ ] Booking(2차)
- [x] MCP Gateway — 봉투·승인 정책·타임아웃·재시도·감사 로그 (Part 12 §3·4·7·8·9·11)
> 오케스트레이터 연결 완료 — chat이 도구를 선택·호출하고, 승인 필수 도구는
> waiting_for_approval 작업(payload)으로 만들어 PATCH 승인 시 실행된다 (docs/09).

## Phase 6 - AI
- [x] System Prompt (`prompts/system_prompt.md` — 서버가 실제 로드)
- [◐] Memory Retrieval — 키워드 ILIKE. 벡터 검색으로 교체 예정
- [x] Planner/Tool Selection — 오케스트레이터 (LLM function-calling 최대 6라운드,
  Bedrock Claude Sonnet 5로 실검증 / 키 없을 때 규칙 라우터 폴백)
- [x] Response Generator — LLM이 도구 결과를 문장으로 합성. 라운드 한도 시에도
  도구 없이 한 번 더 불러 정리한다 (음성으로 읽히므로 "한도 도달" 같은 문구 금지)

## Phase 7 - Security
- [◐] OAuth — 서버측 검증 완료(S1~S4), IdP·로그인 플로우 미착수
- [ ] HTTPS  - [ ] Secret Manager  - [ ] Audit Log 기록 코드

## Phase 8 - Testing
- [x] Unit/API Test (16개, 수용 기준은 Part 18 §1)
- [ ] Integration Test (실 Postgres)  - [ ] Voice Test  - [ ] E2E Test  - [ ] Performance Test

## Phase 9 - Release
- [ ] Alpha  - [ ] Beta  - [ ] v1.0
