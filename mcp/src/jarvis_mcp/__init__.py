"""JARVIS MCP 서버 모음 (docs/12_MCP_Server_Spec.md).

서버 공통 규약 — 새 서버는 반드시 이 규칙을 따른다:

1. 모듈 구조: ``jarvis_mcp/<name>/server.py`` 안에 ``mcp = FastMCP("<name>")``.
2. 도구는 JSON 직렬화 가능한 dict를 반환한다. 도메인 오류는
   ``mcp.server.fastmcp.exceptions.ToolError`` 를 던진다 (게이트웨이가 failed로 매핑).
3. 외부 API 호출은 모듈 수준 작은 함수로 분리해 테스트에서 monkeypatch 가능해야 한다.
   테스트는 네트워크를 사용하지 않는다.
4. 로컬 상태(sqlite 등)는 ``common.data_dir()`` 아래에만 둔다.
5. 승인 정책·타임아웃·재시도·감사 로그는 서버가 아니라 **게이트웨이** 책임이다
   (backend/app/services/mcp_gateway.py). 서버는 도구 실행만 한다.
"""
