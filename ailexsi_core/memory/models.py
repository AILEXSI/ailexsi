from datetime import datetime
from enum import Enum
from uuid import uuid4
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class MemoryType(str, Enum):
    DECISION = "decision"
    HYPOTHESIS = "hypothesis"
    INSIGHT = "insight"
    PROJECT = "project"
    TASK = "task"
    QUESTION = "question"
    FACT = "fact"
    RELATION = "relation"

class MemoryStatus(str, Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    DEPRECATED = "deprecated"
    CONFLICTING = "conflicting"

class RelationType(str, Enum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    LEADS_TO = "leads_to"
    PART_OF = "part_of"
    EVIDENCE_FOR = "evidence_for"

class MemoryEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    type: MemoryType
    project: str = "default"
    content: str
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)
    confidence_reason: Optional[str] = None
    importance: float = Field(ge=0.0, le=1.0, default=0.5)
    expires_at: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)
    priority: float = Field(ge=0.0, le=1.0, default=0.5)
    author: Optional[str] = None
    status: MemoryStatus = MemoryStatus.ACTIVE
    evidence_ids: List[str] = Field(default_factory=list)
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    source: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Relation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    source_id: str
    target_id: str
    relation_type: RelationType
    strength: float = Field(ge=0.0, le=1.0, default=0.8)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    evidence_ids: List[str] = Field(default_factory=list)