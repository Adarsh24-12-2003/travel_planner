from __future__ import annotations
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import date

class TravelRequest(BaseModel):
    origin: str
    destination: str
    start_date: date
    trip_days: int = Field(ge=1, le=30)
    budget_inr: int = Field(ge=5000, le=2_000_000)
    preferences: List[str] = Field(default_factory=list)

    @field_validator("origin", "destination")
    @classmethod
    def non_empty_city(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("City cannot be empty.")
        return v

class ToolResult(BaseModel):
    name: str
    payload: Dict[str, Any]

class Critique(BaseModel):
    score: int = Field(ge=0, le=10)
    issues: List[str] = Field(default_factory=list)
    suggested_fixes: List[str] = Field(default_factory=list)

class AgentState(BaseModel):
    request: TravelRequest
    research: Optional[Dict[str, Any]] = None
    draft_plan: Optional[Dict[str, Any]] = None
    critique: Optional[Critique] = None
    final_plan: Optional[Dict[str, Any]] = None
    revisions_done: int = 0
    errors: List[str] = Field(default_factory=list)
    last_failed_step: Optional[str] = None


def ensure_state(obj) -> AgentState:
    """LangGraph may return a plain dict or a model instance depending on versions.
    This helper normalizes the output to an AgentState instance.
    """
    if isinstance(obj, AgentState):
        return obj
    return AgentState.model_validate(obj)
