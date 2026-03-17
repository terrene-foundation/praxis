# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""
Synchronous database CRUD helpers for the Praxis persistence layer.

Uses raw sqlite3 against DataFlow-created tables. DataFlow handles schema
creation (via ``get_db()`` + ``create_tables_sync()``); this module handles
reads and writes using the same SQLite file.

Each public function calls ``_get_conn()`` which lazily resolves the database
path from ``PraxisConfig.database_url`` and returns a sqlite3 connection.

JSON columns (``constraint_envelope``, ``session_metadata``, ``payload``,
``content``, ``reasoning_trace``, ``constraint_config``) are serialized
to/from JSON strings transparently.
"""

from __future__ import annotations

import json
import logging
import re
import sqlite3
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def _camel_to_snake_plural(name: str) -> str:
    """Convert CamelCase class name to snake_case_plural table name.

    Fallback for older DataFlow versions that don't expose table_name.
    Examples: Session → sessions, DeliberationRecord → deliberation_records
    """
    import re as _re

    s = _re.sub(r"(?<=[a-z0-9])([A-Z])", r"_\1", name)
    s = _re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", s)
    snake = s.lower()
    # Simple English pluralization
    if snake.endswith("y") and not snake.endswith(("ay", "ey", "oy", "uy")):
        return snake[:-1] + "ies"
    if snake.endswith(("s", "x", "z", "ch", "sh")):
        return snake + "es"
    return snake + "s"


# Columns that store JSON dicts — serialized on write, deserialized on read
_JSON_COLUMNS = frozenset(
    {
        "constraint_envelope",
        "session_metadata",
        "payload",
        "content",
        "reasoning_trace",
        "constraint_config",
        "verdict_payload",
        "evidence",
        "current_value",
        "proposed_value",
    }
)


def _db_path() -> str:
    """Extract the filesystem path from the DATABASE_URL config value.

    Handles both ``sqlite:///./path`` (relative) and ``sqlite:////abs/path``
    (absolute) URL formats.
    """
    from praxis.persistence import get_db  # ensures tables exist

    get_db()

    from praxis.config import get_config

    url = get_config().database_url
    # Strip the sqlite:/// prefix to get the filesystem path
    match = re.match(r"sqlite:///(.+)", url)
    if not match:
        raise ValueError(f"Unsupported database URL format: {url}")
    return match.group(1)


def _get_conn() -> sqlite3.Connection:
    """Open a sqlite3 connection with row factory for dict-like access."""
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def _table_name(model_name: str) -> str:
    """Convert a DataFlow model class name to its SQL table name.

    DataFlow uses snake_case plural: Session → sessions,
    DeliberationRecord → deliberation_records, etc.
    """
    from praxis.persistence import get_db

    db = get_db()
    # DataFlow API compatibility: newer versions use db.models (list of ModelDefinition),
    # older/PyPI versions use db._class_name_to_table_name() or db._models dict.
    if hasattr(db, "models") and db.models:
        for m in db.models:
            if m.name == model_name:
                return m.table_name
    if hasattr(db, "_class_name_to_table_name"):
        return db._class_name_to_table_name(model_name)
    if hasattr(db, "_models") and model_name in db._models:
        # Fall back to convention: CamelCase → snake_case_plural
        return _camel_to_snake_plural(model_name)
    raise ValueError(f"Model '{model_name}' not registered with DataFlow")


def _serialize(data: dict) -> dict:
    """Serialize JSON columns to strings for INSERT/UPDATE."""
    out = {}
    for k, v in data.items():
        if k in _JSON_COLUMNS and v is not None and not isinstance(v, str):
            out[k] = json.dumps(v)
        else:
            out[k] = v
    return out


def _deserialize(row: sqlite3.Row) -> dict:
    """Convert a sqlite3.Row to a dict, deserializing JSON columns."""
    d = dict(row)
    for k in _JSON_COLUMNS:
        if k in d and d[k] is not None and isinstance(d[k], str):
            try:
                d[k] = json.loads(d[k])
            except (json.JSONDecodeError, TypeError):
                pass
    return d


def _now_iso() -> str:
    """UTC ISO 8601 timestamp for manual created_at/updated_at."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


# Regex for valid SQL column names — prevents SQL injection via dict keys.
# Allows letters, digits, and underscores. Must start with a letter or underscore.
# Maximum 63 characters (PostgreSQL limit, conservative for SQLite).
_VALID_COLUMN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]{0,63}$")


def _validate_columns(keys) -> None:
    """Validate that all dict keys are safe SQL column names.

    Raises:
        ValueError: If any key does not match the safe column name pattern.
    """
    for k in keys:
        if not _VALID_COLUMN.match(k):
            raise ValueError(f"Invalid column name: {k!r}")


# ---------------------------------------------------------------------------
# Public CRUD helpers
# ---------------------------------------------------------------------------


def db_create(model_name: str, data: dict) -> dict:
    """Insert a record into the database.

    Auto-stamps ``created_at`` and ``updated_at`` if not present.
    """
    _validate_columns(data.keys())
    row = _serialize(dict(data))
    if "created_at" not in row or not row["created_at"]:
        row["created_at"] = _now_iso()
    if "updated_at" not in row or not row["updated_at"]:
        row["updated_at"] = row["created_at"]

    table = _table_name(model_name)
    cols = ", ".join(row.keys())
    placeholders = ", ".join(["?"] * len(row))
    sql = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"

    conn = _get_conn()
    try:
        conn.execute(sql, list(row.values()))
        conn.commit()
    finally:
        conn.close()

    logger.debug("db_create(%s) id=%s", model_name, data.get("id"))
    return row


def db_read(model_name: str, record_id: str) -> dict | None:
    """Read a single record by primary key (``id``)."""
    table = _table_name(model_name)
    sql = f"SELECT * FROM {table} WHERE id = ?"

    conn = _get_conn()
    try:
        cursor = conn.execute(sql, (record_id,))
        row = cursor.fetchone()
    finally:
        conn.close()

    if row is None:
        logger.debug("db_read(%s, %s) -> not found", model_name, record_id)
        return None

    logger.debug("db_read(%s, %s) -> found", model_name, record_id)
    return _deserialize(row)


def db_update(model_name: str, record_id: str, fields: dict) -> dict:
    """Update specific fields on an existing record.

    Auto-stamps ``updated_at``.
    """
    _validate_columns(fields.keys())
    row = _serialize(dict(fields))
    if "updated_at" not in row:
        row["updated_at"] = _now_iso()

    table = _table_name(model_name)
    set_clause = ", ".join(f"{k} = ?" for k in row.keys())
    sql = f"UPDATE {table} SET {set_clause} WHERE id = ?"

    conn = _get_conn()
    try:
        conn.execute(sql, [*row.values(), record_id])
        conn.commit()
    finally:
        conn.close()

    logger.debug("db_update(%s, %s)", model_name, record_id)
    return {"updated": True, "id": record_id}


def db_list(
    model_name: str,
    filter: dict | None = None,
    limit: int = 100,
    offset: int = 0,
    order_asc: bool = False,
) -> list[dict]:
    """List records with optional field=value filters and pagination.

    Args:
        model_name: DataFlow model class name (e.g. "Session").
        filter: Optional dict of field=value equality filters.
        limit: Maximum records to return.
        offset: Number of records to skip.
        order_asc: If True, order by created_at ascending (oldest first).
            Defaults to False (newest first).
    """
    # Clamp limit and offset to safe ranges
    limit = max(0, min(limit, 10000))
    offset = max(0, offset)

    table = _table_name(model_name)
    params: list = []
    where_parts: list[str] = []

    if filter:
        _validate_columns(filter.keys())
        for k, v in filter.items():
            where_parts.append(f"{k} = ?")
            params.append(v)

    sql = f"SELECT * FROM {table}"
    if where_parts:
        sql += " WHERE " + " AND ".join(where_parts)
    sql += " ORDER BY created_at ASC" if order_asc else " ORDER BY created_at DESC"
    sql += f" LIMIT {limit} OFFSET {offset}"

    conn = _get_conn()
    try:
        cursor = conn.execute(sql, params)
        rows = cursor.fetchall()
    finally:
        conn.close()

    records = [_deserialize(r) for r in rows]
    logger.debug("db_list(%s, filter=%s) -> %d records", model_name, filter, len(records))
    return records


def db_count(model_name: str, filter: dict | None = None) -> int:
    """Count records matching an optional filter."""
    table = _table_name(model_name)
    params: list = []
    where_parts: list[str] = []

    if filter:
        _validate_columns(filter.keys())
        for k, v in filter.items():
            where_parts.append(f"{k} = ?")
            params.append(v)

    sql = f"SELECT COUNT(*) FROM {table}"
    if where_parts:
        sql += " WHERE " + " AND ".join(where_parts)

    conn = _get_conn()
    try:
        cursor = conn.execute(sql, params)
        count = cursor.fetchone()[0]
    finally:
        conn.close()

    logger.debug("db_count(%s, filter=%s) -> %d", model_name, filter, count)
    return count


def db_delete(model_name: str, record_id: str) -> bool:
    """Delete a record by primary key. Returns True if a row was deleted."""
    table = _table_name(model_name)
    sql = f"DELETE FROM {table} WHERE id = ?"

    conn = _get_conn()
    try:
        cursor = conn.execute(sql, (record_id,))
        conn.commit()
        deleted = cursor.rowcount > 0
    finally:
        conn.close()

    logger.debug("db_delete(%s, %s) -> %s", model_name, record_id, deleted)
    return deleted
