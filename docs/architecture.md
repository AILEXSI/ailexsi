# AILEXSI Architecture

## High-Level Overview

AILEXSI acts as an intermediary continuity layer between the user interface, the LLM, and persistent storage.

### Core Components

1. **Memory Extractor**
   - Analyzes conversations, code, decisions
   - Classifies into Memory Types
   - Extracts metadata (confidence, project, relations)

2. **Memory Store** (SQLite)
   - Durable, local-first
   - Full-text search via SQLite FTS5
   - Versioning for updates

3. **Reflection Engine**
   - Periodic synthesis (daily/weekly)
   - Pattern detection
   - Contradiction identification

4. **Knowledge Graph**
   - Entities and relations
   - Conflict detection

5. **Retrieval & Context Builder**
   - Relevance ranking (hybrid semantic + keyword)
   - Continuity-aware prompting

## Data Model

```yaml
MemoryEntry:
  id: uuid
  created_at: timestamp
  updated_at: timestamp
  type: enum[decision, hypothesis, insight, project, task, question, fact, relation]
  project: string
  content: text
  confidence: float (0.0-1.0)
  status: enum[active, resolved, deprecated, conflicting]
  source:
    chat_id: string
    session_id: string
    user_id: string
    model: string
```

## ACP - AILEXSI Continuity Protocol

JSON-based exchange format for memory portability across models and instances.