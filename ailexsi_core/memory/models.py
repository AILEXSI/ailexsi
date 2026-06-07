from datetime import datetime
from enum import Enum
from uuid import uuid4
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Tuple

class MemoryType(str, Enum):
    DECISION = "decision"
    HYPOTHESIS = "hypothesis"
    INSIGHT = "insight"
    PROJECT = "project"
    TASK = "task"
    QUESTION = "question"
    FACT = "fact"
    RELATION = "relation"
    REFLECTION = "reflection"
    PATTERN = "pattern"
    NARRATIVE = "narrative"

class MemoryStatus(str, Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    DEPRECATED = "deprecated"
    CONFLICTING = "conflicting"

class ReflectionType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

class RelationType(str, Enum):
    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"
    LEADS_TO = "leads_to"
    PART_OF = "part_of"
    EVIDENCE_FOR = "evidence_for"

class MemorySource(BaseModel):
    chat_id: Optional[str] = None
    session_id: Optional[str] = None
    model: Optional[str] = None
    user_id: Optional[str] = None
    document: Optional[str] = None

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
    resolved_reason: Optional[str] = None
    source: MemorySource = Field(default_factory=MemorySource)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    parent_id: Optional[str] = None
    version: int = 1

class Relation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    source_id: str
    target_id: str
    relation_type: RelationType
    strength: float = Field(ge=0.0, le=1.0, default=0.8)
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    evidence_ids: List[str] = Field(default_factory=list)

class ReflectionEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    reflection_type: ReflectionType
    project: str = "default"
    based_on_memory_ids: List[str]
    summary: str
    insights: List[str]
    generated_patterns: List[str]
    narrative: str
    confidence: float = Field(ge=0.0, le=1.0, default=0.75)
    evidence_ids: List[str] = Field(default_factory=list)
    time_period: Optional[Tuple[datetime, datetime]] = None

class PatternEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    project: str = "default"
    title: str
    description: str
    confidence: float = Field(ge=0.0, le=1.0, default=0.75)
    evidence_ids: List[str] = Field(default_factory=list)
    reflection_ids: List[str] = Field(default_factory=list)
    status: MemoryStatus = MemoryStatus.ACTIVE
    importance: float = Field(ge=0.0, le=1.0, default=0.7)

class NarrativeEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    project: str = "default"
    title: str
    content: str
    version: int = 1
    parent_id: Optional[str] = None
    reflection_ids: List[str] = Field(default_factory=list)
    pattern_ids: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.7)
    time_period: Optional[Tuple[datetime, datetime]] = None
