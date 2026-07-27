# JARVIS Project
## Part 3. System Architecture

### 목표
JARVIS는 음성 기반 개인 AI 비서 시스템이다.
사용자는 자연스럽게 말하고, 시스템은 이해·계획·실행·보고를 수행한다.

### 전체 구성
```
iPhone App
    │
    ▼
Speech-to-Text (STT)
    │
    ▼
JARVIS Orchestrator
    ├── Memory
    ├── Planner
    ├── MCP Gateway
    ├── Search
    ├── Calendar
    ├── Email
    └── Task Manager
            │
            ▼
Large Language Model
            │
            ▼
Text-to-Speech (TTS)
            │
            ▼
사용자 음성 응답
```

### 앱 구성
- 음성 대화 화면
- 진행 상태 표시
- 대화 기록
- 설정

### 오케스트레이터 역할
- 사용자 의도 분석
- 작업 계획 생성
- 필요한 도구 호출
- 결과 통합
- 자연스러운 음성 보고

### Memory
- 사용자 선호
- 자주 가는 장소
- 반복 일정
- 대화 컨텍스트

### MCP 연동
- 웹 검색
- 일정
- 메일
- 문서
- 향후 예약 시스템

### 보안
- OAuth 기반 인증
- HTTPS 통신
- 최소 권한 원칙
- 민감 정보 암호화

### MVP
1. 음성 대화
2. 웹 검색
3. 메모리
4. 일정 조회
5. 결과 음성 브리핑
