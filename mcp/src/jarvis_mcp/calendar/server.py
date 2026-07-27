"""Calendar MCP 서버 (Part 12 §6) — 로컬 sqlite MVP 스토어.

Google Calendar 연동 전 MVP: 도구 인터페이스는 연동 후에도 유지된다.
도구: search_events / create_event / update_event / delete_event / check_availability

승인 정책(생성·변경·삭제는 사용자 승인 필수)은 게이트웨이 책임이다.
"""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from jarvis_mcp import common

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    starts_at TEXT NOT NULL,
    ends_at TEXT NOT NULL,
    location TEXT,
    description TEXT,
    created_at TEXT,
    updated_at TEXT
);
"""

mcp = FastMCP("calendar")


def _db() -> sqlite3.Connection:
    """호출 시점에 연다 — 테스트가 JARVIS_MCP_DATA를 바꾼 뒤에도 격리되도록."""
    return common.open_db("calendar.db", SCHEMA)


def _parse_iso(value: str, field: str) -> str:
    try:
        datetime.fromisoformat(value)
    except ValueError as exc:
        raise ToolError(f"{field}이(가) 올바른 ISO-8601 형식이 아닙니다: {value}") from exc
    return value


def _event_dict(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)


@mcp.tool()
def search_events(query: str = "", date_from: str = "", date_to: str = "", limit: int = 20) -> dict[str, Any]:
    """일정을 검색한다. query는 제목/설명 부분 일치, date_from/date_to는 시작 시각(ISO-8601) 범위."""
    sql = "SELECT * FROM events WHERE 1=1"
    params: list[Any] = []
    if query:
        sql += " AND (title LIKE ? OR description LIKE ?)"
        like = f"%{query}%"
        params += [like, like]
    if date_from:
        sql += " AND starts_at >= ?"
        params.append(_parse_iso(date_from, "date_from"))
    if date_to:
        sql += " AND starts_at <= ?"
        params.append(_parse_iso(date_to, "date_to"))
    sql += " ORDER BY starts_at LIMIT ?"
    params.append(max(1, limit))

    conn = _db()
    try:
        rows = conn.execute(sql, params).fetchall()
    finally:
        conn.close()
    events = [_event_dict(row) for row in rows]
    return {"events": events, "count": len(events)}


@mcp.tool()
def create_event(
    title: str, starts_at: str, ends_at: str, location: str = "", description: str = ""
) -> dict[str, Any]:
    """일정을 생성한다. starts_at/ends_at은 ISO-8601 (예: '2026-07-27T14:00:00')."""
    _parse_iso(starts_at, "starts_at")
    _parse_iso(ends_at, "ends_at")
    if ends_at <= starts_at:
        raise ToolError("ends_at은 starts_at보다 이후여야 합니다.")

    event_id = str(uuid.uuid4())
    now = common.utcnow_iso()
    conn = _db()
    try:
        conn.execute(
            "INSERT INTO events (id, title, starts_at, ends_at, location, description, created_at, updated_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (event_id, title, starts_at, ends_at, location, description, now, now),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
    finally:
        conn.close()
    return _event_dict(row)


@mcp.tool()
def update_event(
    event_id: str,
    title: str = "",
    starts_at: str = "",
    ends_at: str = "",
    location: str = "",
    description: str = "",
) -> dict[str, Any]:
    """일정을 부분 갱신한다. 빈 문자열이 아닌 필드만 반영된다."""
    updates: dict[str, str] = {}
    if title:
        updates["title"] = title
    if starts_at:
        updates["starts_at"] = _parse_iso(starts_at, "starts_at")
    if ends_at:
        updates["ends_at"] = _parse_iso(ends_at, "ends_at")
    if location:
        updates["location"] = location
    if description:
        updates["description"] = description

    conn = _db()
    try:
        row = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
        if row is None:
            raise ToolError(f"일정을 찾을 수 없습니다: {event_id}")

        new_starts = updates.get("starts_at", row["starts_at"])
        new_ends = updates.get("ends_at", row["ends_at"])
        if new_ends <= new_starts:
            raise ToolError("ends_at은 starts_at보다 이후여야 합니다.")

        if updates:
            updates["updated_at"] = common.utcnow_iso()
            assignments = ", ".join(f"{field} = ?" for field in updates)
            conn.execute(
                f"UPDATE events SET {assignments} WHERE id = ?",
                (*updates.values(), event_id),
            )
            conn.commit()
        row = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
    finally:
        conn.close()
    return _event_dict(row)


@mcp.tool()
def delete_event(event_id: str) -> dict[str, Any]:
    """일정을 삭제한다."""
    conn = _db()
    try:
        cursor = conn.execute("DELETE FROM events WHERE id = ?", (event_id,))
        conn.commit()
    finally:
        conn.close()
    if cursor.rowcount == 0:
        raise ToolError(f"일정을 찾을 수 없습니다: {event_id}")
    return {"deleted": event_id}


@mcp.tool()
def check_availability(starts_at: str, ends_at: str) -> dict[str, Any]:
    """해당 구간이 비어 있는지 확인하고 겹치는 일정을 반환한다."""
    _parse_iso(starts_at, "starts_at")
    _parse_iso(ends_at, "ends_at")
    if ends_at <= starts_at:
        raise ToolError("ends_at은 starts_at보다 이후여야 합니다.")

    conn = _db()
    try:
        rows = conn.execute(
            "SELECT * FROM events WHERE starts_at < ? AND ends_at > ? ORDER BY starts_at",
            (ends_at, starts_at),
        ).fetchall()
    finally:
        conn.close()
    conflicts = [_event_dict(row) for row in rows]
    return {"available": not conflicts, "conflicts": conflicts}
