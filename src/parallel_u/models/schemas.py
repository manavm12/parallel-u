from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field

Depth = Literal["high_level", "technical"]


class PreferencesIn(BaseModel):
    user_id: str = Field(..., min_length=1)
    topics: str = Field(..., min_length=3, description="Comma-separated or free text topics")
    depth: Depth = "high_level"
    time_budget_min: int = Field(5, ge=1, le=30)


class PreferencesOut(BaseModel):
    user_id: str
    topics: str
    depth: Depth
    time_budget_min: int
    updated_at: datetime


class BriefGenerateIn(BaseModel):
    user_id: str = Field(..., min_length=1)


class BriefOut(BaseModel):
    user_id: str
    date: str  # YYYY-MM-DD
    time_budget_min: int
    top_3_things: list[dict]
    one_deeper_insight: str
    one_opportunity: dict
    sources_used: list[dict]
    created_at: datetime
