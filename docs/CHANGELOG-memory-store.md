# Memory Store — documented extension

**Date:** 2026-08-02  
**Agent:** GrokBuild  
**Repo:** `ailexsi`

## Change

Implemented missing `ailexsi_core/memory/store.py` referenced by
`ailexsi_core/memory/__init__.py` (`from .store import AilexsiStore`).

## Why

`__init__.py` already exported `AilexsiStore`, but the module did not exist.
Roadmap v0.1 requires a SQLite backend. Without the store, the core could not
persist memories or export graphs for the vault bridge.

## What was added

- `AilexsiStore` with SQLite tables for:
  - memories
  - relations
  - reflections
  - patterns
  - narratives
- FTS5 search (with LIKE fallback)
- `export_graph(project?)` for vault visualization
- Bulk upsert helpers

## Compatibility

Models in `models.py` are **unchanged**. No RelationType or MemoryType
mutations. Resonance remains out of core until RFC.

## Related

- `docs/vault-bridge.md` — sync protocol with `ailexsi-core-vault`
- Vault seed script may write `data/ailexsi_memory.db` for local demos
