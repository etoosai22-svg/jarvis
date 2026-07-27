# JARVIS Project — Part 25. Project File Tree

> 실제 저장소 구조 (2026-07-27 기준). 계획상 위치가 아니라 **현재 존재하는 것**을 기록한다.

```
JARVIS/
├── README.md
├── PROGRESS.md                  # 세션별 작업 로그
├── .gitignore
├── docs/                        # 설계 문서 (01~25) — 정본
│   └── openapi.json             # API 계약 스냅샷 (Part 9와 동기 유지)
├── prompts/
│   └── system_prompt.md         # 서버가 로드하는 JARVIS 페르소나
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 앱, CORS, lifespan
│   │   ├── api/v1/endpoints/    # chat, voice, tasks, memory
│   │   ├── core/                # config, database, security(JWT), time
│   │   ├── models/              # SQLAlchemy 7테이블
│   │   ├── schemas/             # (빈 스캐폴드 — 현재 Pydantic 모델은 endpoint 파일 안)
│   │   └── services/            # chat_service (대화 파이프라인)
│   ├── migrations/              # Alembic (head: 3bea36f739c5)
│   ├── tests/                   # conftest(임시 DB) + 16 tests
│   ├── alembic.ini
│   ├── docker-compose.yml       # api + postgres + redis
│   ├── Dockerfile               # 빌드 컨텍스트 = 저장소 루트 (prompts/ 포함)
│   ├── pyproject.toml           # uv 관리
│   └── .env.example
├── frontend/                    # Expo 53 + React Navigation + zustand
│   ├── App.tsx
│   └── src/
│       ├── app/AppNavigator.tsx
│       ├── components/          # common, chat/, tasks/, memory/, voice/, settings/, ConnectionNotice
│       ├── config/env.ts        # EXPO_PUBLIC_API_BASE_URL
│       ├── data/mockData.ts     # 오프라인 폴백 전용
│       ├── screens/             # Home, Conversation, Tasks, Memory, Settings
│       ├── services/            # api.ts(클라이언트), mappers.ts(DTO↔모델)
│       ├── store/index.ts       # zustand
│       ├── theme/tokens.ts
│       └── types/               # models.ts(화면), api.ts(DTO), env.d.ts
├── mcp/                         # MCP 서버 5종 (공식 python-sdk, uv 프로젝트)
│   ├── pyproject.toml
│   ├── src/jarvis_mcp/
│   │   ├── __init__.py          # 서버 공통 규약 5개 (새 서버는 이걸 따른다)
│   │   ├── common.py            # data_dir/files_root/open_db/utcnow_iso
│   │   ├── search/  calendar/  notes/  files/  weather/   # 각 server.py
│   └── tests/                   # 서버별 in-memory MCP 세션 테스트 34개
├── scripts/                     # (비어 있음)
├── docker/                      # (비어 있음 — compose는 backend/에 있음)
└── .github/workflows/           # (비어 있음 — CI 추가가 다음 우선순위)
```

## 원칙
- frontend / backend 분리, docs가 계약의 정본 (충돌 시 docs → 코드 순서로 수정)
- prompts: AI 페르소나 버전 관리 — 서버가 파일을 직접 로드하므로 배포 이미지에 포함 필수
- mcp: 서비스별 독립 구성 (Part 12)
- 빈 디렉터리는 "계획된 자리"다 — 채워지기 전까지 이 문서에 (비어 있음)으로 명시한다
