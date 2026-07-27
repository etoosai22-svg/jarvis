"""서버 공통 유틸 — 저장 위치와 시각 규약."""

from __future__ import annotations

import os
import sqlite3
from datetime import UTC, datetime
from pathlib import Path


def data_dir() -> Path:
    """서버 로컬 상태의 루트. 테스트는 JARVIS_MCP_DATA로 격리한다."""
    root = Path(os.environ.get("JARVIS_MCP_DATA", "~/.jarvis/mcp")).expanduser()
    root.mkdir(parents=True, exist_ok=True)
    return root


def files_root() -> Path:
    """files 서버 샌드박스 루트. 이 밖의 경로 접근은 금지된다."""
    root = Path(os.environ.get("JARVIS_FILES_ROOT", str(data_dir() / "files"))).expanduser()
    root.mkdir(parents=True, exist_ok=True)
    return root


def utcnow_iso() -> str:
    """backend와 동일한 naive-UTC ISO 문자열 (docs/09 §0)."""
    return datetime.now(UTC).replace(tzinfo=None).isoformat()


def open_db(name: str, schema: str) -> sqlite3.Connection:
    """서버별 sqlite 연결. 스키마는 멱등(IF NOT EXISTS)이어야 한다."""
    conn = sqlite3.connect(data_dir() / name)
    conn.row_factory = sqlite3.Row
    conn.executescript(schema)
    return conn
