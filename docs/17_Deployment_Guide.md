# JARVIS Project — Part 17. Deployment Guide

## 환경
Local / Development / Staging / Production

## 권장 인프라
Docker / Docker Compose / Nginx / FastAPI / PostgreSQL / Redis / Object Storage / Prometheus+Grafana / Sentry

## CI/CD
Git Push → 테스트 → Docker 빌드 → 보안 검사 → Staging 배포 → 승인 → Production 배포

## 환경 변수
OPENAI_API_KEY / DATABASE_URL / REDIS_URL / JWT_SECRET / MCP_ENDPOINT
(비밀 정보는 Secret Manager 사용, 저장소에 포함 금지)

## Docker 구성
api / worker / postgres / redis / nginx

## 로그
구조화된 JSON / request_id 기반 추적 / 민감정보 마스킹

## 모니터링
API 응답 시간 / WebSocket 연결 수 / MCP 호출 성공률 / CPU·Memory / 오류율

## 백업
PostgreSQL 일일 백업 / 파일 버전 관리 / 복구 테스트 정기 수행

## 장애 대응
Health Check / 자동 재시작 / 롤백 지원 / 장애 알림

## 보안
HTTPS / TLS / 최소 권한 원칙 / API Rate Limit / Secret Rotation

## MVP 완료 기준
Docker Compose 한 번으로 실행 / CI/CD 자동화 / 운영 모니터링 / 백업 및 복구 절차
