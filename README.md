# JARVIS — Personal AI Chief of Staff

> "자비스." → "네, 실장님."

음성 기반 개인 AI 비서실장. FastAPI 백엔드 + React Native(Expo) 앱.

- **다음 세션 인수인계**: [HANDOFF.md](HANDOFF.md) ← 이어서 작업한다면 여기부터
- **설계 문서**: [docs/](docs/README.md) — 계약/방향/현황 3층 구조, 정본 규칙 포함
- **진행 로그**: [PROGRESS.md](PROGRESS.md)
- **진행 현황**: [docs/24_Project_Tasks.md](docs/24_Project_Tasks.md)

## 빠른 시작

### Backend (로컬, SQLite)
```bash
cd backend
uv sync --extra test
uv run uvicorn app.main:app --reload      # http://localhost:8000/docs
```

### Backend (Docker, PostgreSQL)
```bash
cd backend
cp .env.example .env                       # OPENAI_API_KEY 등 채우기
docker compose up --build                  # alembic upgrade 후 기동
```

### Frontend (Expo)
```bash
cd frontend
npm install
# 실기기 테스트 시: EXPO_PUBLIC_API_BASE_URL=http://<개발PC IP>:8000
npm run ios        # 또는 npm start
```

### 테스트
```bash
cd backend && uv run --extra test python -m pytest -q    # 16 tests
cd frontend && npx tsc --noEmit
```

## 구조 요약
```
backend/   FastAPI + SQLAlchemy(async) + Alembic — API 계약: docs/09_API_Spec.md
frontend/  Expo 53 + zustand — 백엔드 미가동 시 목업 폴백 + 경고 배너
prompts/   서버가 로드하는 시스템 프롬프트
docs/      설계 문서 정본 (01~25)
mcp/       Phase 5 스캐폴드 (미착수, 명세: docs/12_MCP_Server_Spec.md)
```

## 운영 배포 전 필수
- `AUTH_REQUIRED=true` + OAuth 발급자 설정 (로컬 기본값은 무인증)
- `AUTO_CREATE_TABLES=false` + `alembic upgrade head`
- HTTPS 종단, 비밀키는 Secret Manager — [docs/19_Security_Guide.md](docs/19_Security_Guide.md)
