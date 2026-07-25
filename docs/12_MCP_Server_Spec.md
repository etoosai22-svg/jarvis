# JARVIS Project
## Part 12. MCP Server Specification

### 1. 전체 구조
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

### 2. MCP Gateway 책임
- 사용 가능한 MCP 서버 목록 관리
- 도구 호출 요청 전달 / 응답 정규화
- 타임아웃 및 재시도 처리
- 감사 로그 기록 / 권한 검증

### 3. 공통 도구 호출 형식
요청:
```json
{
  "request_id": "uuid",
  "user_id": "uuid",
  "session_id": "uuid",
  "server": "calendar",
  "tool": "search_events",
  "arguments": { "start_date": "2026-07-25", "end_date": "2026-07-31" },
  "approval_required": false
}
```
응답:
```json
{
  "request_id": "uuid",
  "status": "success",
  "data": {},
  "error": null,
  "metadata": { "latency_ms": 420, "source": "google_calendar" }
}
```

### 4. 표준 상태값
success / partial_success / failed / approval_required / unauthorized / timeout / rate_limited

### 5. MCP 서버별 주요 도구

#### Search
search_web, search_news, search_products, search_tickets, extract_summary

#### Calendar
search_events, create_event, update_event, delete_event, check_availability
> 생성·변경·삭제는 사용자 최종 승인 필요

#### Email
search_messages, read_message, create_draft, reply_message, send_message
> 전송은 반드시 사용자 최종 승인 필요

#### Files
list_files, read_file, create_file, update_file, delete_file

#### Maps
search_place, get_directions, estimate_time, search_nearby

#### Weather
get_current, get_forecast, get_alerts

#### Notes
list_notes, read_note, create_note, update_note, search_notes

#### Booking (향후)
search_availability, create_reservation

### 6. 오류 처리 원칙
- 실패 시 대체 경로 탐색
- 승인 필요 작업은 중단 후 사용자 확인
- 모든 외부 호출 감사 로그 기록
