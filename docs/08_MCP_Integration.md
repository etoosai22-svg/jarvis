# JARVIS Project
## Part 8. MCP Integration

### 연동 서비스 (MVP)
- 웹 검색
- Google Calendar
- Gmail
- 문서 (Google Docs / Notion)

### 향후 확장
- 네이버/카카오 예약
- 항공/KTX 조회
- 지도 / 경로

### 구조
iPhone App → JARVIS API → MCP Gateway → External Services

### 원칙
- 최소 권한
- OAuth 기반
- 실패 시 대안 제시
