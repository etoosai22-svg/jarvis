# JARVIS Project — Part 22. Codex Development Instructions

## 역할
Codex는 시니어 소프트웨어 엔지니어처럼 행동한다.

## 우선순위
정확성 > 유지보수성 > 테스트 가능성 > 성능 > 보안

## 개발 원칙
TypeScript/Python 타입 적극 활용 / 작은 단위 구현 / 테스트와 함께 개발
하드코딩 금지 / 환경변수 사용 / 민감정보 로그 금지

## 구현 순서
- Phase 1: 프로젝트 초기화, CI, Docker, 기본 API
- Phase 2: 인증, 대화 API, WebSocket, 음성 처리
- Phase 3: Memory, MCP Gateway, Search, Calendar
- Phase 4: Tasks, 승인 시스템, 알림, 파일 처리

## 코드 규칙
함수는 단일 책임 / 비즈니스 로직은 Service 계층 / Route는 얇게 / 공개 함수 타입 명시 / 공통 예외 처리기

## PR 기준
테스트 통과 / 린트 통과 / 문서 업데이트 / Breaking Change 명시

## 산출물 (작업 완료 시)
변경 파일 목록 / 구현 내용 요약 / 테스트 결과 / 남은 작업 / 위험 요소

## 금지 사항
추측 구현 / 불필요한 의존성 / 비밀키 커밋 / 테스트 없이 완료 처리
