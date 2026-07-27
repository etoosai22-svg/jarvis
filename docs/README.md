# JARVIS — Personal AI Chief of Staff

> "자비스." → "네, 실장님."

음성 기반 개인 AI 비서실장. 말 한마디로 조사·분석·제안·보고를 수행한다.

## 문서 운영 규칙 (정본 규칙)

1. **이 디렉터리(`~/JARVIS/docs`)가 유일한 정본이다.** 다른 곳의 사본은 참고용이며 수정하지 않는다.
2. 문서에는 두 층이 있다:
   - **계약(contract)** — 09(API), 13(DB), 12(MCP), 19 §0(보안 불변식): 코드가 이 문서를 위반하면 **코드가 버그**다. 동작을 바꾸려면 문서 먼저 수정.
   - **방향(direction)** — 나머지: 목표와 범위를 말하며, 구현 세부는 계약 문서에 위임한다.
3. 구현이 문서에 없는 것을 필요로 하면(새 필드·새 엔드포인트), **먼저 계약 문서에 추가**하고 구현한다. "발명 후 미기록"이 지금까지 드리프트의 주 원인이었다.
4. 상태 표기: 계약 문서 안의 미구현 항목은 "현재 상태" 블록으로 명시한다. 24(Tasks)가 전체 진행 현황의 정본이다.
5. 문서 번호 02는 결번이다 (역사적 이유, 재사용하지 않는다).

## 문서 목록

| # | 파일 | 층 | 내용 |
|---|------|----|------|
| 01 | 01_Vision.md | 방향 | 프로젝트 비전 + UX 원칙 |
| 03 | 03_System_Architecture.md | 방향 | 전체 시스템 구조 |
| 04 | 04_AI_Behavior.md | 방향 | AI 행동 명세 |
| 05 | 05_Memory_System.md | 방향 | 메모리 시스템 설계 |
| 06 | 06_Voice_Interface.md | 방향 | 음성 인터페이스 설계 |
| 07 | 07_App_UI.md | 방향 | 앱 UI/UX |
| 08 | 08_MCP_Integration.md | 방향 | MCP 연동 설계 |
| 09 | 09_API_Spec.md | **계약** | REST/WS API 명세 (+ openapi.json 스냅샷) |
| 10 | 10_Development_Roadmap.md | 방향 | 개발 로드맵 + 기술 스택 |
| 11 | 11_System_Prompt.md | 방향 | 페르소나 (실행본은 `/prompts/system_prompt.md`) |
| 12 | 12_MCP_Server_Spec.md | **계약** | MCP 서버·도구·승인 정책 명세 |
| 13 | 13_Database_Schema.md | **계약** | DB 스키마 (Alembic과 동기) |
| 14 | 14_Frontend_Development_Guide.md | 방향 | 프론트엔드 개발 가이드 |
| 15 | 15_Backend_Development_Guide.md | 방향 | 백엔드 개발 가이드 |
| 16 | 16_Prompt_Engineering.md | 방향 | 프롬프트 엔지니어링 |
| 17 | 17_Deployment_Guide.md | 방향 | 배포 가이드 |
| 18 | 18_Testing_Strategy.md | **계약** | 수용 기준 + 테스트 현황 |
| 19 | 19_Security_Guide.md | **계약**(§0) | 보안 불변식 + 원칙 |
| 20 | 20_Release_Plan.md | 방향 | 릴리스 계획 |
| 21 | 21_Master_PRD.md | 방향 | 마스터 PRD |
| 22 | 22_Codex_Development_Instructions.md | 방향 | 개발 에이전트 지침 |
| 23 | 23_Claude_Code_Instructions.md | 방향 | 개발 에이전트 지침 |
| 24 | 24_Project_Tasks.md | **현황** | Phase별 진행 상태 (체크 = 검증된 코드) |
| 25 | 25_Project_File_Tree.md | **현황** | 실제 저장소 구조 |

## 기술 스택
- **App**: React Native (Expo 53, iOS + Android)
- **Backend**: FastAPI (Python 3.12, uv)
- **LLM**: OpenAI API (서버 측 전용)
- **DB**: SQLite(로컬) / PostgreSQL 15(운영) + Redis(도입 예정) + Vector DB(Phase 3)

## MVP 목표 (2~4주)
1. 음성 대화 (STT/TTS)
2. 웹 검색
3. 메모리
4. 일정 조회
5. 음성 브리핑
