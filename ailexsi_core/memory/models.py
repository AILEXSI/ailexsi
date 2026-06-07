from datetime import datetime
from enum import Enum
from uuid import uuid4
from pydantic import BaseModel, Field
from typing import Optional, Dict

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

class MemoryEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    type: MemoryType
    project: str
    content: str
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)
    status: MemoryStatus = MemoryStatus.ACTIVE
    source: Dict = Field(default_factory=dict)
    metadata: Dict = Field(default_factory=dict)