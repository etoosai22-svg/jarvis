# JARVIS Project — Part 18. Testing Strategy

## 테스트 단계
1. **Unit Test**: 서비스 로직, 메모리 처리, 승인 정책, MCP 호출 래퍼
2. **Integration Test**: PostgreSQL, Redis, MCP Gateway, WebSocket
3. **API Test**: REST API, 인증, 권한, 오류 응답
4. **Voice Flow Test**: STT 입력 → 의도 분석 → MCP 실행 → TTS 출력
5. **End-to-End Test**: 음성 요청부터 결과 브리핑까지 전체 흐름

## 성능 테스트 목표
- 일반 API: 1초 이내
- 첫 음성 응답: 2초 이내
- 동시 사용자 / WebSocket 부하 / MCP 응답 시간 / DB 쿼리 / 메모리 사용량

## 보안 테스트
인증 우회 / 권한 상승 / API Rate Limit / 비밀키 노출 / 입력값 검증

## 테스트 데이터
샘플 사용자 / 샘플 일정 / 샘플 메모리 / Mock MCP 서버

## 자동화
Git Push 시 테스트 실행 / PR 생성 시 통합 테스트 / 배포 전 E2E 테스트

## 성공 기준
Unit Test 90%+ / 핵심 API 통합 테스트 통과 / 음성 시나리오 정상 동작 / 주요 MCP 연동 검증 / E2E 통과
