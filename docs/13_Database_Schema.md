# JARVIS Project
## Part 13. Database Schema

### 기술 스택
- PostgreSQL: 관계형 데이터
- Redis: 캐시 및 세션
- Vector DB: 의미 기반 메모리 검색
- Object Storage: 파일 저장

### 주요 테이블

#### users
- id (UUID), name, preferred_name, locale, timezone, created_at

#### conversations
- id, user_id, session_id, started_at, ended_at

#### messages
- id, conversation_id, role (user/assistant), content, created_at

#### tasks
- id, user_id, title, status, priority, created_at, completed_at

#### memories
- id, user_id, category, content, embedding_id, confidence, updated_at

#### preferences
- id, user_id, key, value

#### audit_logs
- id, user_id, action, target, result, created_at

### Redis 사용
- 세션 캐시
- 진행 중인 작업
- 음성 스트리밍 상태
- Rate Limit

### Vector DB
저장 대상: 장기 기억, 프로젝트 정보, 사용자 선호, 과거 대화 요약
인덱스: user_id, session_id, created_at, status

### 백업
- PostgreSQL 일일 백업
- Object Storage 버전 관리
- 감사 로그 장기 보관

### MVP 필수 테이블
1. users
2. conversations
3. messages
4. tasks
5. memories
