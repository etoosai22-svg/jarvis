# JARVIS — Personal AI Chief of Staff

> "자비스." → "네, 실장님."

음성 기반 개인 AI 비서실장. 말 한마디로 조사·분석·제안·보고를 수행한다.

## 문서 목록

| 파일 | 내용 |
|------|------|
| 01_Vision.md | 프로젝트 비전 + UX 원칙 |
| 03_System_Architecture.md | 전체 시스템 구조 |
| 04_AI_Behavior.md | AI 행동 명세 |
| 05_Memory_System.md | 메모리 시스템 설계 |
| 06_Voice_Interface.md | 음성 인터페이스 설계 |
| 07_App_UI.md | 앱 UI/UX |
| 08_MCP_Integration.md | MCP 연동 설계 |
| 09_API_Spec.md | API 명세 |
| 10_Development_Roadmap.md | 개발 로드맵 + 기술 스택 |

## 기술 스택
- **App**: React Native (iOS + Android)
- **Backend**: FastAPI (Python)
- **LLM**: OpenAI API
- **DB**: PostgreSQL + Redis + Vector DB

## MVP 목표 (2~4주)
1. 음성 대화 (STT/TTS)
2. 웹 검색
3. 메모리
4. 일정 조회
5. 음성 브리핑
