from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastmcp import FastMCP
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

DB_PATH = os.getenv("STORAGE_DB_PATH", "/memory/storage.db")
AUDIT_PATH = os.getenv("STORAGE_AUDIT_PATH", "/memory/storage-audit.log")

ALLOWED_CLASSIFICATIONS = {"public", "internal", "confidential", "secret"}
WRITE_CLASSIFICATIONS = {"public", "internal"}
PROJECT_ID_PATTERN = re.compile(r"^[A-Za-z0-9-]+$")

mcp = FastMCP("storage")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_parent(path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def get_db() -> sqlite3.Connection:
    """Open the persistent SQLite database and ensure its schema exists."""
    ensure_parent(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS entries (
            entry_id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            entry_type TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            classification TEXT NOT NULL,
            deleted INTEGER NOT NULL DEFAULT 0,
            last_updated TEXT NOT NULL
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_entries_project_type "
        "ON entries(project_id, entry_type, deleted)"
    )
    return conn


def audit(
    operation: str,
    project_id: str,
    entry_id: str | None,
    classification: str | None,
    calling_role: str | None,
) -> None:
    """Append one JSON audit record. Agents have no tool that edits this file."""
    ensure_parent(AUDIT_PATH)
    record: dict[str, Any] = {
        "timestamp": utc_now(),
        "operation": operation,
        "project_id": project_id,
        "entry_id": entry_id,
        "classification": classification,
        "calling_role": calling_role or "unknown",
    }
    with open(AUDIT_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")


def validate_project_id(project_id: str) -> None:
    if not PROJECT_ID_PATTERN.match(project_id or ""):
        raise ValueError("project_id must contain only letters, numbers, and hyphens")


def validate_nonempty(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


def validate_classification(classification: str) -> None:
    if classification not in ALLOWED_CLASSIFICATIONS:
        raise ValueError(
            f"classification must be one of {sorted(ALLOWED_CLASSIFICATIONS)}"
        )
    if classification not in WRITE_CLASSIFICATIONS:
        raise ValueError(
            "this server does not accept writes classified confidential or secret"
        )


def get_live_entry(conn: sqlite3.Connection, project_id: str, entry_id: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM entries WHERE project_id = ? AND entry_id = ? AND deleted = 0",
        (project_id, entry_id),
    ).fetchone()


@mcp.tool
def write_entry(
    project_id: str,
    entry_type: str,
    title: str,
    content: str,
    classification: str,
    calling_role: str = "unknown",
) -> dict:
    """Write a new entry to the store. Requires a valid classification tag."""
    validate_project_id(project_id)
    validate_nonempty(entry_type, "entry_type")
    validate_nonempty(title, "title")
    validate_nonempty(content, "content")
    validate_classification(classification)

    entry_id = str(uuid.uuid4())
    now = utc_now()
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO entries (entry_id, project_id, entry_type, title, content, "
            "classification, last_updated) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (entry_id, project_id, entry_type, title, content, classification, now),
        )
        conn.commit()
    finally:
        conn.close()

    audit("write_entry", project_id, entry_id, classification, calling_role)
    return {"entry_id": entry_id}


@mcp.tool
def read_entry(project_id: str, entry_id: str) -> dict:
    """Read a single entry by ID, scoped to its project."""
    validate_project_id(project_id)
    validate_nonempty(entry_id, "entry_id")

    conn = get_db()
    try:
        row = get_live_entry(conn, project_id, entry_id)
    finally:
        conn.close()

    if row is None:
        raise ValueError("no entry found for that project_id and entry_id")
    return dict(row)


@mcp.tool
def list_entries(project_id: str, entry_type: str | None = None) -> list[dict]:
    """List entries for a project. Metadata only; never returns full content."""
    validate_project_id(project_id)

    conn = get_db()
    try:
        if entry_type is None:
            rows = conn.execute(
                "SELECT entry_id, title, entry_type, classification, last_updated "
                "FROM entries WHERE project_id = ? AND deleted = 0 "
                "ORDER BY last_updated DESC",
                (project_id,),
            ).fetchall()
        else:
            validate_nonempty(entry_type, "entry_type")
            rows = conn.execute(
                "SELECT entry_id, title, entry_type, classification, last_updated "
                "FROM entries WHERE project_id = ? AND entry_type = ? AND deleted = 0 "
                "ORDER BY last_updated DESC",
                (project_id, entry_type),
            ).fetchall()
    finally:
        conn.close()

    return [dict(row) for row in rows]


@mcp.tool
def update_entry(
    project_id: str,
    entry_id: str,
    content: str,
    calling_role: str = "unknown",
) -> dict:
    """Update the content of an existing entry. Classification is preserved."""
    validate_project_id(project_id)
    validate_nonempty(entry_id, "entry_id")
    validate_nonempty(content, "content")

    now = utc_now()
    conn = get_db()
    try:
        row = get_live_entry(conn, project_id, entry_id)
        if row is None:
            raise ValueError("no entry found to update")
        conn.execute(
            "UPDATE entries SET content = ?, last_updated = ? "
            "WHERE project_id = ? AND entry_id = ? AND deleted = 0",
            (content, now, project_id, entry_id),
        )
        conn.commit()
        classification = row["classification"]
    finally:
        conn.close()

    audit("update_entry", project_id, entry_id, classification, calling_role)
    return {"success": True}


@mcp.tool
def delete_entry(
    project_id: str,
    entry_id: str,
    calling_role: str = "unknown",
) -> dict:
    """Soft-delete an entry. Marks deleted; does not remove backend evidence."""
    validate_project_id(project_id)
    validate_nonempty(entry_id, "entry_id")

    conn = get_db()
    try:
        row = get_live_entry(conn, project_id, entry_id)
        if row is None:
            raise ValueError("no entry found to delete")
        conn.execute(
            "UPDATE entries SET deleted = 1, last_updated = ? "
            "WHERE project_id = ? AND entry_id = ? AND deleted = 0",
            (utc_now(), project_id, entry_id),
        )
        conn.commit()
        classification = row["classification"]
    finally:
        conn.close()

    audit("delete_entry", project_id, entry_id, classification, calling_role)
    return {"success": True}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Persistent storage MCP server")
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    import uvicorn
    app = mcp.http_app(
        stateless_http=True,
        middleware=[
            Middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
        ],
    )
    uvicorn.run(app, host=args.host, port=args.port)


#!/usr/bin/env python3
"""Sample storage MCP server with role-based allow-list enforcement."""

import datetime
import json
import os
from pathlib import Path
from typing import Any

try:
    from fastmcp import FastMCP
    from fastmcp.exceptions import ToolError
except Exception:  # pragma: no cover - lets tests run without FastMCP installed
    class ToolError(Exception):
        pass
    class FastMCP:
        def __init__(self, name: str):
            self.name = name
        def tool(self, func=None):
            def decorate(fn):
                return fn
            return decorate(func) if func else decorate
        def run(self):
            print(f"FastMCP not installed; {self.name} functions are importable only.")

mcp = FastMCP("storage")
CALLING_ROLE = os.environ.get("AGENT_ROLE", "")
ALLOW_LIST_PATH = Path(__file__).parent / "allow-list.json"
ALLOW_LIST = json.loads(ALLOW_LIST_PATH.read_text(encoding="utf-8"))
AUDIT_LOG_PATH = Path(os.environ.get("STORAGE_AUDIT_LOG", "logs/storage-audit-log.jsonl"))
AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
STORE_PATH = Path(os.environ.get("STORAGE_STORE", "logs/storage-store.json"))
STORE_PATH.parent.mkdir(parents=True, exist_ok=True)


def _load_store() -> dict[str, Any]:
    if STORE_PATH.exists():
        return json.loads(STORE_PATH.read_text(encoding="utf-8"))
    return {}


def _save_store(data: dict[str, Any]) -> None:
    STORE_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _record(event: str, operation: str, outcome: str, detail: str | None = None) -> dict[str, Any]:
    record = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "event": event,
        "operation": operation,
        "role": CALLING_ROLE,
        "outcome": outcome,
        "detail": detail,
        "policy_reference": "docs/governance-policy.md",
    }
    with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as log:
        log.write(json.dumps(record) + "\n")
    return record


def _authorize(operation: str) -> None:
    allowed_roles = ALLOW_LIST.get(operation, [])
    if CALLING_ROLE not in allowed_roles:
        record = _record("authorization_denied", operation, "authorization_denied")
        raise ToolError(
            f"authorization_denied: role '{record['role']}' may not call "
            f"'{operation}'. See {record['policy_reference']}."
        )


@mcp.tool
def write_entry(key: str, value: str) -> dict:
    _authorize("write_entry")
    data = _load_store()
    data[key] = value
    _save_store(data)
    _record("storage_write", "write_entry", "success")
    return {"ok": True, "key": key}


@mcp.tool
def read_entry(key: str) -> dict:
    _authorize("read_entry")
    data = _load_store()
    _record("storage_read", "read_entry", "success")
    return {"key": key, "value": data.get(key)}


@mcp.tool
def list_entries() -> dict:
    _authorize("list_entries")
    data = _load_store()
    _record("storage_list", "list_entries", "success")
    return {"keys": sorted(data)}


@mcp.tool
def update_entry(key: str, value: str) -> dict:
    _authorize("update_entry")
    data = _load_store()
    data[key] = value
    _save_store(data)
    _record("storage_update", "update_entry", "success")
    return {"ok": True, "key": key}


@mcp.tool
def delete_entry(key: str) -> dict:
    _authorize("delete_entry")
    data = _load_store()
    existed = key in data
    data.pop(key, None)
    _save_store(data)
    _record("storage_delete", "delete_entry", "success")
    return {"ok": True, "deleted": existed}


@mcp.tool
def audit_read(limit: int = 50) -> dict:
    _authorize("audit_read")
    if not AUDIT_LOG_PATH.exists():
        return {"entries": []}
    lines = AUDIT_LOG_PATH.read_text(encoding="utf-8").splitlines()[-limit:]
    return {"entries": [json.loads(line) for line in lines if line.strip()]}


if __name__ == "__main__":
    mcp.run()
