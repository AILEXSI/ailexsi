"""
AILEXSI Memory Store — local-first SQLite backend.

Single source of truth for MemoryEntry, Relation, ReflectionEntry,
PatternEntry, and NarrativeEntry. Designed for Continuity over Intelligence.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Generator, Iterable, List, Optional, Sequence, Union

from .models import (
    MemoryEntry,
    MemoryStatus,
    MemoryType,
    NarrativeEntry,
    PatternEntry,
    ReflectionEntry,
    Relation,
    RelationType,
)


def _dt_to_iso(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    return value.isoformat()


def _iso_to_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    return datetime.fromisoformat(value)


def _dumps(obj: Any) -> str:
    return json.dumps(obj, default=str, ensure_ascii=False)


def _loads(raw: Optional[str], default: Any = None) -> Any:
    if raw is None or raw == "":
        return default if default is not None else {}
    return json.loads(raw)


class AilexsiStore:
    """SQLite-backed memory store (local-first, FTS-ready)."""

    def __init__(self, db_path: Union[str, Path] = "ailexsi_memory.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _conn(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._conn() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    type TEXT NOT NULL,
                    project TEXT NOT NULL DEFAULT 'default',
                    content TEXT NOT NULL,
                    confidence REAL NOT NULL DEFAULT 0.8,
                    confidence_reason TEXT,
                    importance REAL NOT NULL DEFAULT 0.5,
                    expires_at TEXT,
                    tags TEXT NOT NULL DEFAULT '[]',
                    priority REAL NOT NULL DEFAULT 0.5,
                    author TEXT,
                    status TEXT NOT NULL DEFAULT 'active',
                    evidence_ids TEXT NOT NULL DEFAULT '[]',
                    resolved_by TEXT,
                    resolved_at TEXT,
                    resolved_reason TEXT,
                    source TEXT NOT NULL DEFAULT '{}',
                    metadata TEXT NOT NULL DEFAULT '{}',
                    parent_id TEXT,
                    version INTEGER NOT NULL DEFAULT 1
                );

                CREATE TABLE IF NOT EXISTS relations (
                    id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    relation_type TEXT NOT NULL,
                    strength REAL NOT NULL DEFAULT 0.8,
                    confidence REAL NOT NULL DEFAULT 0.8,
                    created_at TEXT NOT NULL,
                    evidence_ids TEXT NOT NULL DEFAULT '[]'
                );

                CREATE TABLE IF NOT EXISTS reflections (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    reflection_type TEXT NOT NULL,
                    project TEXT NOT NULL DEFAULT 'default',
                    based_on_memory_ids TEXT NOT NULL DEFAULT '[]',
                    summary TEXT NOT NULL,
                    insights TEXT NOT NULL DEFAULT '[]',
                    generated_patterns TEXT NOT NULL DEFAULT '[]',
                    narrative TEXT NOT NULL DEFAULT '',
                    confidence REAL NOT NULL DEFAULT 0.75,
                    evidence_ids TEXT NOT NULL DEFAULT '[]',
                    time_period TEXT
                );

                CREATE TABLE IF NOT EXISTS patterns (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    project TEXT NOT NULL DEFAULT 'default',
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    confidence REAL NOT NULL DEFAULT 0.75,
                    evidence_ids TEXT NOT NULL DEFAULT '[]',
                    reflection_ids TEXT NOT NULL DEFAULT '[]',
                    status TEXT NOT NULL DEFAULT 'active',
                    importance REAL NOT NULL DEFAULT 0.7
                );

                CREATE TABLE IF NOT EXISTS narratives (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    project TEXT NOT NULL DEFAULT 'default',
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    version INTEGER NOT NULL DEFAULT 1,
                    parent_id TEXT,
                    reflection_ids TEXT NOT NULL DEFAULT '[]',
                    pattern_ids TEXT NOT NULL DEFAULT '[]',
                    confidence REAL NOT NULL DEFAULT 0.7,
                    time_period TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_memories_project ON memories(project);
                CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(type);
                CREATE INDEX IF NOT EXISTS idx_memories_status ON memories(status);
                CREATE INDEX IF NOT EXISTS idx_relations_source ON relations(source_id);
                CREATE INDEX IF NOT EXISTS idx_relations_target ON relations(target_id);

                -- Standalone FTS index (no external-content sync; avoids corruption
                -- when bulk-writing from vault import). Populated explicitly.
                CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                    id UNINDEXED,
                    content,
                    project,
                    tags
                );
                """
            )

    # ------------------------------------------------------------------
    # MemoryEntry
    # ------------------------------------------------------------------

    def upsert_memory(self, entry: MemoryEntry) -> MemoryEntry:
        entry.updated_at = datetime.utcnow()
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO memories (
                    id, created_at, updated_at, type, project, content,
                    confidence, confidence_reason, importance, expires_at,
                    tags, priority, author, status, evidence_ids,
                    resolved_by, resolved_at, resolved_reason, source,
                    metadata, parent_id, version
                ) VALUES (
                    ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
                )
                ON CONFLICT(id) DO UPDATE SET
                    updated_at=excluded.updated_at,
                    type=excluded.type,
                    project=excluded.project,
                    content=excluded.content,
                    confidence=excluded.confidence,
                    confidence_reason=excluded.confidence_reason,
                    importance=excluded.importance,
                    expires_at=excluded.expires_at,
                    tags=excluded.tags,
                    priority=excluded.priority,
                    author=excluded.author,
                    status=excluded.status,
                    evidence_ids=excluded.evidence_ids,
                    resolved_by=excluded.resolved_by,
                    resolved_at=excluded.resolved_at,
                    resolved_reason=excluded.resolved_reason,
                    source=excluded.source,
                    metadata=excluded.metadata,
                    parent_id=excluded.parent_id,
                    version=excluded.version
                """,
                (
                    entry.id,
                    _dt_to_iso(entry.created_at),
                    _dt_to_iso(entry.updated_at),
                    entry.type.value,
                    entry.project,
                    entry.content,
                    entry.confidence,
                    entry.confidence_reason,
                    entry.importance,
                    _dt_to_iso(entry.expires_at),
                    _dumps(entry.tags),
                    entry.priority,
                    entry.author,
                    entry.status.value,
                    _dumps(entry.evidence_ids),
                    entry.resolved_by,
                    _dt_to_iso(entry.resolved_at),
                    entry.resolved_reason,
                    _dumps(entry.source.model_dump()),
                    _dumps(entry.metadata),
                    entry.parent_id,
                    entry.version,
                ),
            )
            # Maintain FTS (best-effort)
            try:
                conn.execute("DELETE FROM memories_fts WHERE id = ?", (entry.id,))
                conn.execute(
                    "INSERT INTO memories_fts(id, content, project, tags) VALUES (?,?,?,?)",
                    (entry.id, entry.content, entry.project, " ".join(entry.tags)),
                )
            except sqlite3.DatabaseError:
                # Search still works via LIKE fallback
                pass
        return entry

    def get_memory(self, memory_id: str) -> Optional[MemoryEntry]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM memories WHERE id = ?", (memory_id,)
            ).fetchone()
        return self._row_to_memory(row) if row else None

    def list_memories(
        self,
        project: Optional[str] = None,
        memory_type: Optional[MemoryType] = None,
        status: Optional[MemoryStatus] = None,
        limit: int = 500,
    ) -> List[MemoryEntry]:
        clauses: List[str] = []
        params: List[Any] = []
        if project:
            clauses.append("project = ?")
            params.append(project)
        if memory_type:
            clauses.append("type = ?")
            params.append(memory_type.value)
        if status:
            clauses.append("status = ?")
            params.append(status.value)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)
        with self._conn() as conn:
            rows = conn.execute(
                f"SELECT * FROM memories {where} ORDER BY updated_at DESC LIMIT ?",
                params,
            ).fetchall()
        return [self._row_to_memory(r) for r in rows]

    def search_memories(self, query: str, limit: int = 50) -> List[MemoryEntry]:
        with self._conn() as conn:
            try:
                rows = conn.execute(
                    """
                    SELECT m.* FROM memories_fts f
                    JOIN memories m ON m.id = f.id
                    WHERE memories_fts MATCH ?
                    LIMIT ?
                    """,
                    (query, limit),
                ).fetchall()
                if rows:
                    return [self._row_to_memory(r) for r in rows]
            except sqlite3.DatabaseError:
                pass
            like = f"%{query}%"
            rows = conn.execute(
                """
                SELECT * FROM memories
                WHERE content LIKE ? OR project LIKE ? OR tags LIKE ?
                ORDER BY updated_at DESC LIMIT ?
                """,
                (like, like, like, limit),
            ).fetchall()
        return [self._row_to_memory(r) for r in rows]

    def delete_memory(self, memory_id: str) -> bool:
        with self._conn() as conn:
            try:
                conn.execute("DELETE FROM memories_fts WHERE id = ?", (memory_id,))
            except sqlite3.DatabaseError:
                pass
            cur = conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            return cur.rowcount > 0

    def _row_to_memory(self, row: sqlite3.Row) -> MemoryEntry:
        data = dict(row)
        from .models import MemorySource

        return MemoryEntry(
            id=data["id"],
            created_at=_iso_to_dt(data["created_at"]) or datetime.utcnow(),
            updated_at=_iso_to_dt(data["updated_at"]) or datetime.utcnow(),
            type=MemoryType(data["type"]),
            project=data["project"],
            content=data["content"],
            confidence=data["confidence"],
            confidence_reason=data.get("confidence_reason"),
            importance=data["importance"],
            expires_at=_iso_to_dt(data.get("expires_at")),
            tags=_loads(data.get("tags"), []),
            priority=data["priority"],
            author=data.get("author"),
            status=MemoryStatus(data["status"]),
            evidence_ids=_loads(data.get("evidence_ids"), []),
            resolved_by=data.get("resolved_by"),
            resolved_at=_iso_to_dt(data.get("resolved_at")),
            resolved_reason=data.get("resolved_reason"),
            source=MemorySource(**_loads(data.get("source"), {})),
            metadata=_loads(data.get("metadata"), {}),
            parent_id=data.get("parent_id"),
            version=data["version"],
        )

    # ------------------------------------------------------------------
    # Relations
    # ------------------------------------------------------------------

    def upsert_relation(self, relation: Relation) -> Relation:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO relations (
                    id, source_id, target_id, relation_type, strength,
                    confidence, created_at, evidence_ids
                ) VALUES (?,?,?,?,?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET
                    source_id=excluded.source_id,
                    target_id=excluded.target_id,
                    relation_type=excluded.relation_type,
                    strength=excluded.strength,
                    confidence=excluded.confidence,
                    evidence_ids=excluded.evidence_ids
                """,
                (
                    relation.id,
                    relation.source_id,
                    relation.target_id,
                    relation.relation_type.value,
                    relation.strength,
                    relation.confidence,
                    _dt_to_iso(relation.created_at),
                    _dumps(relation.evidence_ids),
                ),
            )
        return relation

    def list_relations(
        self,
        source_id: Optional[str] = None,
        target_id: Optional[str] = None,
        relation_type: Optional[RelationType] = None,
    ) -> List[Relation]:
        clauses: List[str] = []
        params: List[Any] = []
        if source_id:
            clauses.append("source_id = ?")
            params.append(source_id)
        if target_id:
            clauses.append("target_id = ?")
            params.append(target_id)
        if relation_type:
            clauses.append("relation_type = ?")
            params.append(relation_type.value)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._conn() as conn:
            rows = conn.execute(
                f"SELECT * FROM relations {where} ORDER BY created_at DESC",
                params,
            ).fetchall()
        return [self._row_to_relation(r) for r in rows]

    def _row_to_relation(self, row: sqlite3.Row) -> Relation:
        data = dict(row)
        return Relation(
            id=data["id"],
            source_id=data["source_id"],
            target_id=data["target_id"],
            relation_type=RelationType(data["relation_type"]),
            strength=data["strength"],
            confidence=data["confidence"],
            created_at=_iso_to_dt(data["created_at"]) or datetime.utcnow(),
            evidence_ids=_loads(data.get("evidence_ids"), []),
        )

    # ------------------------------------------------------------------
    # Reflections / Patterns / Narratives
    # ------------------------------------------------------------------

    def upsert_reflection(self, entry: ReflectionEntry) -> ReflectionEntry:
        period = None
        if entry.time_period:
            period = [_dt_to_iso(entry.time_period[0]), _dt_to_iso(entry.time_period[1])]
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO reflections (
                    id, created_at, reflection_type, project, based_on_memory_ids,
                    summary, insights, generated_patterns, narrative, confidence,
                    evidence_ids, time_period
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET
                    summary=excluded.summary,
                    insights=excluded.insights,
                    generated_patterns=excluded.generated_patterns,
                    narrative=excluded.narrative,
                    confidence=excluded.confidence,
                    evidence_ids=excluded.evidence_ids,
                    time_period=excluded.time_period
                """,
                (
                    entry.id,
                    _dt_to_iso(entry.created_at),
                    entry.reflection_type.value,
                    entry.project,
                    _dumps(entry.based_on_memory_ids),
                    entry.summary,
                    _dumps(entry.insights),
                    _dumps(entry.generated_patterns),
                    entry.narrative,
                    entry.confidence,
                    _dumps(entry.evidence_ids),
                    _dumps(period) if period else None,
                ),
            )
        return entry

    def list_reflections(self, project: Optional[str] = None) -> List[ReflectionEntry]:
        with self._conn() as conn:
            if project:
                rows = conn.execute(
                    "SELECT * FROM reflections WHERE project = ? ORDER BY created_at DESC",
                    (project,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM reflections ORDER BY created_at DESC"
                ).fetchall()
        return [self._row_to_reflection(r) for r in rows]

    def _row_to_reflection(self, row: sqlite3.Row) -> ReflectionEntry:
        from .models import ReflectionType

        data = dict(row)
        period_raw = _loads(data.get("time_period"), None)
        time_period = None
        if period_raw and len(period_raw) == 2:
            a, b = _iso_to_dt(period_raw[0]), _iso_to_dt(period_raw[1])
            if a and b:
                time_period = (a, b)
        return ReflectionEntry(
            id=data["id"],
            created_at=_iso_to_dt(data["created_at"]) or datetime.utcnow(),
            reflection_type=ReflectionType(data["reflection_type"]),
            project=data["project"],
            based_on_memory_ids=_loads(data.get("based_on_memory_ids"), []),
            summary=data["summary"],
            insights=_loads(data.get("insights"), []),
            generated_patterns=_loads(data.get("generated_patterns"), []),
            narrative=data.get("narrative") or "",
            confidence=data["confidence"],
            evidence_ids=_loads(data.get("evidence_ids"), []),
            time_period=time_period,
        )

    def upsert_pattern(self, entry: PatternEntry) -> PatternEntry:
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO patterns (
                    id, created_at, project, title, description, confidence,
                    evidence_ids, reflection_ids, status, importance
                ) VALUES (?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET
                    title=excluded.title,
                    description=excluded.description,
                    confidence=excluded.confidence,
                    evidence_ids=excluded.evidence_ids,
                    reflection_ids=excluded.reflection_ids,
                    status=excluded.status,
                    importance=excluded.importance
                """,
                (
                    entry.id,
                    _dt_to_iso(entry.created_at),
                    entry.project,
                    entry.title,
                    entry.description,
                    entry.confidence,
                    _dumps(entry.evidence_ids),
                    _dumps(entry.reflection_ids),
                    entry.status.value,
                    entry.importance,
                ),
            )
        return entry

    def list_patterns(self, project: Optional[str] = None) -> List[PatternEntry]:
        with self._conn() as conn:
            if project:
                rows = conn.execute(
                    "SELECT * FROM patterns WHERE project = ? ORDER BY importance DESC",
                    (project,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM patterns ORDER BY importance DESC"
                ).fetchall()
        return [self._row_to_pattern(r) for r in rows]

    def _row_to_pattern(self, row: sqlite3.Row) -> PatternEntry:
        data = dict(row)
        return PatternEntry(
            id=data["id"],
            created_at=_iso_to_dt(data["created_at"]) or datetime.utcnow(),
            project=data["project"],
            title=data["title"],
            description=data["description"],
            confidence=data["confidence"],
            evidence_ids=_loads(data.get("evidence_ids"), []),
            reflection_ids=_loads(data.get("reflection_ids"), []),
            status=MemoryStatus(data["status"]),
            importance=data["importance"],
        )

    def upsert_narrative(self, entry: NarrativeEntry) -> NarrativeEntry:
        entry.updated_at = datetime.utcnow()
        period = None
        if entry.time_period:
            period = [_dt_to_iso(entry.time_period[0]), _dt_to_iso(entry.time_period[1])]
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO narratives (
                    id, created_at, updated_at, project, title, content,
                    version, parent_id, reflection_ids, pattern_ids,
                    confidence, time_period
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET
                    updated_at=excluded.updated_at,
                    title=excluded.title,
                    content=excluded.content,
                    version=excluded.version,
                    parent_id=excluded.parent_id,
                    reflection_ids=excluded.reflection_ids,
                    pattern_ids=excluded.pattern_ids,
                    confidence=excluded.confidence,
                    time_period=excluded.time_period
                """,
                (
                    entry.id,
                    _dt_to_iso(entry.created_at),
                    _dt_to_iso(entry.updated_at),
                    entry.project,
                    entry.title,
                    entry.content,
                    entry.version,
                    entry.parent_id,
                    _dumps(entry.reflection_ids),
                    _dumps(entry.pattern_ids),
                    entry.confidence,
                    _dumps(period) if period else None,
                ),
            )
        return entry

    def list_narratives(self, project: Optional[str] = None) -> List[NarrativeEntry]:
        with self._conn() as conn:
            if project:
                rows = conn.execute(
                    "SELECT * FROM narratives WHERE project = ? ORDER BY updated_at DESC",
                    (project,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM narratives ORDER BY updated_at DESC"
                ).fetchall()
        return [self._row_to_narrative(r) for r in rows]

    def _row_to_narrative(self, row: sqlite3.Row) -> NarrativeEntry:
        data = dict(row)
        period_raw = _loads(data.get("time_period"), None)
        time_period = None
        if period_raw and len(period_raw) == 2:
            a, b = _iso_to_dt(period_raw[0]), _iso_to_dt(period_raw[1])
            if a and b:
                time_period = (a, b)
        return NarrativeEntry(
            id=data["id"],
            created_at=_iso_to_dt(data["created_at"]) or datetime.utcnow(),
            updated_at=_iso_to_dt(data["updated_at"]) or datetime.utcnow(),
            project=data["project"],
            title=data["title"],
            content=data["content"],
            version=data["version"],
            parent_id=data.get("parent_id"),
            reflection_ids=_loads(data.get("reflection_ids"), []),
            pattern_ids=_loads(data.get("pattern_ids"), []),
            confidence=data["confidence"],
            time_period=time_period,
        )

    # ------------------------------------------------------------------
    # Graph export (for vault / visualization)
    # ------------------------------------------------------------------

    def export_graph(self, project: Optional[str] = None) -> dict:
        memories = self.list_memories(project=project, limit=5000)
        mem_ids = {m.id for m in memories}
        relations = self.list_relations()
        if project:
            relations = [
                r
                for r in relations
                if r.source_id in mem_ids or r.target_id in mem_ids
            ]
        return {
            "nodes": [
                {
                    "id": m.id,
                    "type": m.type.value,
                    "project": m.project,
                    "status": m.status.value,
                    "content": m.content[:200],
                    "importance": m.importance,
                    "confidence": m.confidence,
                    "tags": m.tags,
                }
                for m in memories
            ],
            "edges": [
                {
                    "id": r.id,
                    "source": r.source_id,
                    "target": r.target_id,
                    "type": r.relation_type.value,
                    "strength": r.strength,
                    "confidence": r.confidence,
                }
                for r in relations
            ],
        }

    def bulk_upsert_memories(self, entries: Sequence[MemoryEntry]) -> int:
        for e in entries:
            self.upsert_memory(e)
        return len(entries)

    def bulk_upsert_relations(self, relations: Sequence[Relation]) -> int:
        for r in relations:
            self.upsert_relation(r)
        return len(relations)
