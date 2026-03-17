# Praxis Persistence

## Overview

DataFlow persistence using raw sqlite3 for CRUD operations. DataFlow handles schema creation; `db_ops.py` handles reads and writes using the same SQLite file.

## Key Files

| File                      | Purpose                            |
| ------------------------- | ---------------------------------- |
| `persistence/__init__.py` | `get_db()`, `create_tables_sync()` |
| `persistence/models.py`   | 9 DataFlow model definitions       |
| `persistence/db_ops.py`   | Sync CRUD helpers (raw sqlite3)    |
| `persistence/queries.py`  | Higher-level query patterns        |
| `persistence/archive.py`  | Session export/import              |

## 9 Models

Session, DeliberationRecord, ConstraintEvent, TrustChainEntry, Workspace, HeldAction, LearningObservation, LearningPattern, LearningEvolutionProposal.

### Conventions

- Primary key: `id: str` (you provide the UUID)
- No `created_at`/`updated_at` on models -- DataFlow manages these
- JSON fields use `Optional[str]` (not `Optional[dict]`)
- Use `db.models` (not `db._models`)

## db_ops API

```python
db_create("Session", {"id": "uuid", ...})
db_read("Session", "uuid")          # -> dict | None
db_update("Session", "uuid", {...}) # auto-stamps updated_at
db_list("Session", filter={...}, limit=100, offset=0, order_asc=False)
db_count("Session", filter={...})
db_delete("Session", "uuid")        # -> bool
```

## Security

- Column name validation: regex `^[a-zA-Z_][a-zA-Z0-9_]{0,63}$` prevents SQL injection
- Parameterized queries: all values use `?` placeholders
- JSON columns: auto-serialized on write, deserialized on read
- Limit clamping: `db_list` clamps limit to [0, 10000]
