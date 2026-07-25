# JARVIS Project — Part 25. Project File Tree

```
JARVIS/
├── README.md
├── docs/
│   ├── 01_Project_Vision.md
│   ├── ...
│   └── 25_Project_File_Tree.md
├── frontend/
│   ├── src/
│   ├── assets/
│   └── package.json
├── backend/
│   ├── app/
│   ├── tests/
│   ├── migrations/
│   └── pyproject.toml
├── mcp/
│   ├── search/
│   ├── calendar/
│   ├── files/
│   ├── notes/
│   └── weather/
├── prompts/
│   ├── system/
│   ├── developer/
│   └── task/
├── scripts/
├── docker/
├── .github/
│   └── workflows/
├── docker-compose.yml
└── LICENSE
```

## 원칙
- frontend / backend 분리
- docs: 설계 문서 관리
- prompts: AI 프롬프트 버전 관리
- mcp: 서비스별 독립 구성
- GitHub Actions: .github/workflows
