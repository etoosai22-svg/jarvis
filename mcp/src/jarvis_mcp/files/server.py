"""Files MCP 서버 (Part 12 §6) — common.files_root() 샌드박스 안의 파일만 다룬다.

도구: search_files / read_file / summarize_file / create_file / update_file
계약: 삭제·외부 전송 금지 / 접근 권한 검증 필수 — 삭제 도구는 구현하지 않는다.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from jarvis_mcp.common import files_root

mcp = FastMCP("files")


def _root() -> Path:
    return files_root().resolve()


def _resolve(rel_path: str) -> Path:
    """사용자 제공 경로를 샌드박스 안으로 해석한다.

    절대경로 입력, "../" 탈출, 심볼릭 링크 탈출을 모두 차단한다
    (resolve()가 심볼릭 링크를 따라간 최종 경로를 검사하므로).
    """
    root = _root()
    candidate = (root / rel_path).resolve()
    if candidate == root or not candidate.is_relative_to(root):
        raise ToolError("샌드박스 밖 경로는 접근할 수 없습니다")
    return candidate


def _rel(path: Path) -> str:
    return path.resolve().relative_to(_root()).as_posix()


def _modified_at(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=UTC).replace(tzinfo=None).isoformat()


def _read_text(path: Path) -> str:
    if not path.is_file():
        raise ToolError(f"파일이 없습니다: {_rel(path)}")
    return path.read_text(encoding="utf-8", errors="replace")


@mcp.tool()
def search_files(pattern: str = "*", content_query: str = "", limit: int = 50) -> dict[str, Any]:
    """샌드박스 안에서 파일을 찾는다. pattern은 glob (예: '*.md'), content_query가 있으면 텍스트 내용도 검색한다."""
    root = _root()
    limit = max(1, min(limit, 500))
    files: list[dict[str, Any]] = []
    for path in sorted(root.rglob(pattern)):
        if not path.is_file():
            continue
        resolved = path.resolve()
        if not resolved.is_relative_to(root):
            continue  # 심볼릭 링크 탈출은 결과에서 제외
        if content_query:
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue  # 텍스트가 아니거나 읽을 수 없으면 스킵
            if content_query not in text:
                continue
        files.append(
            {"path": path.relative_to(root).as_posix(), "size": path.stat().st_size, "modified_at": _modified_at(path)}
        )
        if len(files) >= limit:
            break
    return {"files": files, "count": len(files)}


@mcp.tool()
def read_file(path: str, max_chars: int = 20000) -> dict[str, Any]:
    """샌드박스 안의 텍스트 파일을 읽는다 (utf-8, 최대 max_chars자)."""
    target = _resolve(path)
    text = _read_text(target)
    truncated = len(text) > max_chars
    return {
        "path": _rel(target),
        "content": text[:max_chars],
        "truncated": truncated,
        "size": target.stat().st_size,
    }


@mcp.tool()
def summarize_file(path: str, max_chars: int = 1500) -> dict[str, Any]:
    """파일 앞부분을 발췌해 요약 재료를 제공한다. 의미 요약은 오케스트레이터(LLM)가 수행한다."""
    target = _resolve(path)
    text = _read_text(target)
    return {
        "path": _rel(target),
        "excerpt": text[:max_chars],
        "line_count": len(text.splitlines()),
        "size": target.stat().st_size,
        "note": "발췌입니다. 의미 요약은 오케스트레이터(LLM)가 수행합니다.",
    }


@mcp.tool()
def create_file(path: str, content: str) -> dict[str, Any]:
    """샌드박스 안에 새 파일을 만든다. 이미 존재하면 오류 (덮어쓰기는 update_file)."""
    target = _resolve(path)
    if target.exists():
        raise ToolError(f"이미 존재하는 파일입니다 (덮어쓰기는 update_file): {_rel(target)}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return {"path": _rel(target), "size": target.stat().st_size}


@mcp.tool()
def update_file(path: str, content: str) -> dict[str, Any]:
    """샌드박스 안의 기존 파일 내용을 교체한다. 없으면 오류 (새 파일은 create_file)."""
    target = _resolve(path)
    if not target.is_file():
        raise ToolError(f"존재하지 않는 파일입니다 (새 파일은 create_file): {path}")
    target.write_text(content, encoding="utf-8")
    return {"path": _rel(target), "size": target.stat().st_size}
