"""Notes MCP 서버 (Part 12 §6) — sqlite 로컬 저장.

도구: create_note / search_notes / update_note / archive_note
"""

from __future__ import annotations

import contextlib
import sqlite3
import uuid
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from jarvis_mcp import common

TAG_SEP = "\x1f"  # backend 규약과 동일 — 태그 본문에 쉼표 허용

SCHEMA = """
CREATE TABLE IF NOT EXISTS notes (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    tags TEXT DEFAULT '',
    archived INTEGER DEFAULT 0,
    created_at TEXT,
    updated_at TEXT
);
"""

mcp = FastMCP("notes")


def _db() -> sqlite3.Connection:
    """호출 시점에 연결 — import 시점에 DB를 열지 않는다."""
    return common.open_db("notes.db", SCHEMA)


def _encode_tags(tags: list[str]) -> str:
    return TAG_SEP.join(tags)


def _decode_tags(raw: str) -> list[str]:
    return [tag for tag in (raw or "").split(TAG_SEP) if tag]


def _row_to_note(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "title": row["title"],
        "content": row["content"],
        "tags": _decode_tags(row["tags"]),
        "archived": bool(row["archived"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _get_note(conn: sqlite3.Connection, note_id: str) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    if row is None:
        raise ToolError(f"노트를 찾을 수 없습니다: {note_id}")
    return row


@mcp.tool()
def create_note(title: str, content: str, tags: list[str] = []) -> dict[str, Any]:
    """노트를 생성한다. tags는 자유 문자열 목록 (쉼표 포함 가능)."""
    note_id = str(uuid.uuid4())
    now = common.utcnow_iso()
    with contextlib.closing(_db()) as conn:
        conn.execute(
            "INSERT INTO notes (id, title, content, tags, archived, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, 0, ?, ?)",
            (note_id, title, content, _encode_tags(list(tags)), now, now),
        )
        conn.commit()
        return _row_to_note(_get_note(conn, note_id))


@mcp.tool()
def search_notes(
    query: str = "", tag: str = "", include_archived: bool = False, limit: int = 20
) -> dict[str, Any]:
    """노트를 검색한다. query는 title/content 부분 일치, tag는 정확 일치 필터."""
    sql = "SELECT * FROM notes WHERE 1=1"
    params: list[Any] = []
    if query:
        sql += " AND (title LIKE ? OR content LIKE ?)"
        like = f"%{query}%"
        params += [like, like]
    if not include_archived:
        sql += " AND archived = 0"
    sql += " ORDER BY updated_at DESC"
    with contextlib.closing(_db()) as conn:
        rows = conn.execute(sql, params).fetchall()
    notes = [_row_to_note(row) for row in rows]
    if tag:
        notes = [note for note in notes if tag in note["tags"]]
    notes = notes[: max(0, limit)]
    return {"notes": notes, "count": len(notes)}


@mcp.tool()
def update_note(
    note_id: str, title: str = "", content: str = "", tags: list[str] | None = None
) -> dict[str, Any]:
    """노트를 부분 갱신한다. 빈 값이 아닌 필드만 반영한다 (tags는 None이 아니면 교체)."""
    fields: list[str] = []
    params: list[Any] = []
    if title:
        fields.append("title = ?")
        params.append(title)
    if content:
        fields.append("content = ?")
        params.append(content)
    if tags is not None:
        fields.append("tags = ?")
        params.append(_encode_tags(list(tags)))
    with contextlib.closing(_db()) as conn:
        _get_note(conn, note_id)  # 없는 id면 ToolError
        if fields:
            fields.append("updated_at = ?")
            params.append(common.utcnow_iso())
            conn.execute(f"UPDATE notes SET {', '.join(fields)} WHERE id = ?", (*params, note_id))
            conn.commit()
        return _row_to_note(_get_note(conn, note_id))


@mcp.tool()
def archive_note(note_id: str) -> dict[str, Any]:
    """노트를 보관 처리한다. 이미 보관된 노트여도 성공한다."""
    with contextlib.closing(_db()) as conn:
        _get_note(conn, note_id)  # 없는 id면 ToolError
        conn.execute(
            "UPDATE notes SET archived = 1, updated_at = ? WHERE id = ?",
            (common.utcnow_iso(), note_id),
        )
        conn.commit()
    return {"archived": note_id}
