# Vault Bridge Protocol

**Status:** Active  
**Repos:** `ailexsi` (core) ↔ `ailexsi-core-vault` (UI + Markdown)

## Principle

- **Core (`ailexsi_core/memory`)** remains the Single Source of Truth for structured memory.
- **Vault** is the visual + interaction layer: Markdown files, graph, editor, import pipelines.
- Continuity over Intelligence: every link must be explainable.

## Direction of Truth

```
Python Core (SQLite)  <──sync──>  Vault Markdown (YAML frontmatter)
       ↑                                    ↑
   authoritative                       human-editable
```

1. Core → Vault: export memories as Markdown notes (seed / refresh).
2. Vault → Core: import reviewed notes as MemoryEntry / Relation (human-in-the-loop).
3. Never auto-commit high-impact reflections without review (RFC 0002).

## Frontmatter Schema (Vault Markdown)

```yaml
---
id: <uuid>
type: decision | hypothesis | insight | project | task | question | fact | relation | reflection | pattern | narrative
status: active | resolved | deprecated | conflicting
project: <slug>
confidence: 0.0-1.0
confidence_reason: string?
importance: 0.0-1.0
priority: 0.0-1.0
tags: []
author: string?
evidence_ids: []
parent_id: string?
version: 1
source:
  chat_id: string?
  session_id: string?
  model: string?
  user_id: string?
  document: string?
relations:
  - target_id: <uuid>
    relation_type: supports | contradicts | leads_to | part_of | evidence_for
    strength: 0.0-1.0
    confidence: 0.0-1.0
    reason: string   # truthful linking: why this edge exists
vault_only:
  resonance: false   # soft UI hint; not a core RelationType until RFC
---

# Title

Body markdown...
```

## Relation Types (Core only)

| Type | Meaning |
|------|---------|
| `supports` | Source strengthens target claim |
| `contradicts` | Source conflicts with target |
| `leads_to` | Causal or temporal progression |
| `part_of` | Hierarchical containment |
| `evidence_for` | Source is evidence for target |

**Resonance** appears in vault UI as a soft label only. Until a core RFC accepts it, map resonance-like links to `supports` or `evidence_for` with an explicit `reason`.

## Sync API (planned)

```python
from ailexsi_core.memory import AilexsiStore

store = AilexsiStore("data/ailexsi_memory.db")
graph = store.export_graph(project="ailexsi-core")
# write graph["nodes"] → vault/20_memories/*.md
# write graph["edges"] → vault/30_relations/*.md
```

## Reflection (RFC 0002)

Reflections are first-class:

- Stored as `ReflectionEntry` in core
- Mirrored as notes under `vault/40_reflections/`
- Require human review before bulk confidence changes

## File Layout (Vault Repo)

See `ailexsi-core-vault/vault/README.md`.
