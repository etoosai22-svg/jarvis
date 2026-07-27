# JARVIS Project
## Part 16. Prompt Engineering Guide

### 프롬프트 계층
1. **System Prompt**: 역할, 행동 원칙, 보안 규칙
2. **Developer Prompt**: 구현 정책, MCP 사용 규칙, 출력 형식
3. **Memory Prompt**: 사용자 선호, 장기 기억, 현재 컨텍스트
4. **Task Prompt**: 현재 수행할 작업, 성공 조건, 제약 사항
5. **User Prompt**: 사용자의 실제 요청

### 응답 절차
의도 분석 → 필요 정보 확인 → Memory 조회 → MCP 도구 선택
→ 실행 계획 생성 → 결과 검증 → 자연어 브리핑

### 출력 원칙
- 결론부터 제시 / 근거 제공 / 불확실성 명시 / 다음 행동 제안

### MCP 호출 규칙
- 필요한 도구만 호출
- 동일 작업 중복 호출 금지
- 실패 시 대체 경로 탐색
- 승인 필요 작업은 사용자 확인

### 메모리 활용 대상
사용자 선호 / 반복 업무 / 이전 프로젝트 / 일정 / 즐겨찾기

### 금지 사항
허위 정보 생성 / 확인되지 않은 완료 보고 / 민감정보 노출 / 승인 없는 결제·예약

### 버전 관리
prompt_version / model_version / created_at / updated_at / changelog
