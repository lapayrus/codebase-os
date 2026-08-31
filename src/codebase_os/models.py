from datetime import datetime, timezone
from typing import Literal
from pydantic import BaseModel, Field


def now() -> datetime:
    return datetime.now(timezone.utc)


class Evidence(BaseModel):
    repository: str
    commit: str
    path: str
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    snippet: str
    kind: Literal["source", "structure", "memory", "history"] = "source"
    relevance: float = 0.0


class Claim(BaseModel):
    text: str
    confidence: Literal["high", "medium", "low"]
    evidence_ids: list[int] = Field(default_factory=list)


class Answer(BaseModel):
    question: str
    answer: str
    claims: list[Claim]
    evidence: list[Evidence]
    caveats: list[str] = Field(default_factory=list)
    repository: str
    commit: str
    tokens_estimate: int
    generated_at: datetime = Field(default_factory=now)


class Memory(BaseModel):
    id: str
    repository: str
    text: str
    memory_type: Literal["decision", "convention", "gotcha", "open_question", "ownership"]
    source: Literal["human", "system"] = "human"
    created_at: datetime = Field(default_factory=now)
    updated_at: datetime = Field(default_factory=now)
    stale: bool = False


class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    repository: str | None = None
    top_k: int = Field(default=8, ge=1, le=20)


class MemoryRequest(BaseModel):
    repository: str
    text: str = Field(min_length=3, max_length=2000)
    memory_type: Literal["decision", "convention", "gotcha", "open_question", "ownership"]

