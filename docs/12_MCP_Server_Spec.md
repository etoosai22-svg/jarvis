# JARVIS Project — Part 12. MCP Server Specification

> **구현 상태 (2026-07-27):** MVP 1차 5종(Search/Calendar/Notes/Files/Weather) 구현 완료 — `mcp/src/jarvis_mcp/<name>/server.py` (공식 MCP python-sdk FastMCP, 테스트 34개).
> 게이트웨이는 `backend/app/services/mcp_gateway.py` — §4 봉투, §7 승인 정책, §8 타임아웃 재시도(1회), §9 타임아웃, §11 감사 로그 구현 (테스트 7개).
> 현재 서버는 **in-process 실행**이며 stdio 분리 시에도 `invoke()` 인터페이스는 유지된다.
> 명세 대비 축소분: Search의 search_products/search_tickets 미구현(2차), Calendar/Notes는 외부 연동 전 로컬 sqlite 스토어(도구 인터페이스는 동일), Weather 특보는 제공자 부재로 빈 목록, 오케스트레이터 연결(§2의 Orchestrator 단계)은 다음 작업.

## 1. 목적
JARVIS가 외부 서비스와 상호작용하기 위한 MCP 서버 구조, 책임, 도구 명세, 호출 규칙, 오류 처리 및 보안 기준을 정의한다.

## 2. 전체 구조
```
iPhone App → JARVIS API Server → JARVIS Orchestrator → MCP Gateway
├── Search MCP Server
├── Calendar MCP Server
├── Email MCP Server
├── Files MCP Server
├── Maps MCP Server
├── Weather MCP Server
├── Notes MCP Server
└── Booking MCP Server
```

## 3. MCP Gateway 책임
사용 가능한 MCP 서버 목록 관리 / 연결 상태 확인 / 도구 스키마 조회
도구 호출 요청 전달 / 응답 정규화 / 타임아웃 및 재시도 처리
감사 로그 기록 / 권한 검증 / 민감 작업 승인 여부 확인

## 4. 공통 도구 호출 형식
요청: `{ request_id, user_id, session_id, server, tool, arguments, approval_required }`
응답: `{ request_id, status, data, error, metadata: { latency_ms, source, executed_at } }`

## 5. 표준 상태값
success / partial_success / failed / approval_required / unauthorized / timeout / rate_limited

## 6. MCP 서버별 주요 도구

### Search
search_web, search_news, search_products, search_tickets, open_result, extract_summary

### Calendar
search_events, create_event, update_event, delete_event, check_availability
> 생성·변경·삭제: 사용자 승인 필수

### Email
search_messages, read_message, create_draft, reply_message, send_message
> 전송: 사용자 승인 필수 / 초안 작성: 승인 불필요

### Files
search_files, read_file, summarize_file, create_file, update_file
> 삭제·외부 전송 금지 / 접근 권한 검증 필수

### Maps
search_places, get_route, estimate_travel_time, search_nearby

### Weather
get_current_weather, get_hourly_forecast, get_daily_forecast, get_weather_alerts

### Notes
create_note, search_notes, update_note, archive_note

### Booking (2차)
search_train_tickets, search_flights, search_hotels, search_event_tickets, prepare_booking, confirm_booking
> 초기: 조사·추천까지만 / 실제 예약·결제는 사용자 승인 필수

## 7. 승인 정책
- **승인 불필요**: 검색, 읽기, 비교, 요약, 초안 작성, 추천
- **승인 필수**: 결제, 예약 확정, 일정 생성·변경, 메일 전송, 파일 삭제, 개인정보 외부 전달

## 8. 오류 처리
- 네트워크 오류: 최대 2회 재시도
- 타임아웃: 최대 1회
- 인증 오류: 재시도 없음
- 사용량 제한: 대체 도구 또는 사용자 안내

## 9. 타임아웃 기준
검색 15초 / 일정·메일 10초 / 파일 읽기 30초 / 예약 조사 30초 / 결제·확정 60초

## 10. 보안
OAuth 2.0 / 토큰 암호화 / 최소 권한 / 감사 로그 / 사용자별 격리 / TLS / 비밀키 미노출

## 11. 로깅
모든 도구 호출: user_id, session_id, request_id, server, tool, 실행시각, 성공여부, 소요시간, 승인여부, 오류코드 (민감값 마스킹)

## 12. MVP 범위 (1차)
Search / Calendar / Notes / Weather / Files
Email·Booking은 2차 버전에서 추가
