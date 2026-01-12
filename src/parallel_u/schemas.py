"""Pydantic schemas for Parallel U MVP."""

from pydantic import BaseModel, Field
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# Request/Response schemas for /v1/run endpoint
# ─────────────────────────────────────────────────────────────────────────────


class RunRequest(BaseModel):
    user_id: str = Field(..., description="Unique user identifier")
    topics: list[str] = Field(..., description="List of topics/interests to explore")
    depth: str = Field(
        default="medium",
        description="Depth preference: 'shallow', 'medium', or 'deep'",
    )
    time_budget_min: int = Field(
        default=5, description="Time budget in minutes for exploration"
    )


class TopFinding(BaseModel):
    title: str = Field(..., description="Title of the finding")
    summary: str = Field(..., description="2-4 sentence summary")
    why_it_matters: str = Field(
        ..., description="Why this matters to this specific user"
    )
    source_link: str = Field(..., description="URL to the source")


class BriefOutput(BaseModel):
    top_3_things: list[TopFinding] = Field(
        ..., description="Top 3 most relevant findings"
    )
    one_deeper_insight: str = Field(
        ..., description="Non-obvious pattern or implication across findings"
    )
    one_opportunity: str = Field(
        ...,
        description="Specific action (tool to try, repo to check, idea to explore) with link if available",
    )
    sources_used: list[str] = Field(..., description="List of URLs consulted")


class RunResponse(BaseModel):
    goal: str = Field(..., description="The exploration goal for this session")
    brief: BriefOutput = Field(..., description="The condensed intelligence brief")
    session_id: str = Field(..., description="Session ID for follow-up chat")
    debug: Optional[dict] = Field(
        default=None, description="Debug information (optional)"
    )


# ─────────────────────────────────────────────────────────────────────────────
# OpenAI Planner schemas
# ─────────────────────────────────────────────────────────────────────────────


class BrowsingTask(BaseModel):
    website: str = Field(..., description="Website URL to browse")
    instructions: str = Field(
        ..., description="Specific browsing instructions for Mino"
    )


class PlannerOutput(BaseModel):
    goal: str = Field(..., description="The exploration goal for today")
    tasks: list[BrowsingTask] = Field(
        ..., description="List of browsing tasks to execute"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Chat endpoint schemas
# ─────────────────────────────────────────────────────────────────────────────


class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Session ID from the run response")
    message: str = Field(..., description="User's question about the findings")


class ChatResponse(BaseModel):
    response: str = Field(..., description="AI response to the question")
    session_id: str = Field(..., description="Session ID for continued chat")


# ─────────────────────────────────────────────────────────────────────────────
# Synthesize endpoint schema
# ─────────────────────────────────────────────────────────────────────────────


class SynthesizeRequest(BaseModel):
    user_id: str = Field(..., description="Unique user identifier")
    goal: str = Field(..., description="The exploration goal")
    topics: list[str] = Field(..., description="List of topics explored")
    browsing_results: list[dict] = Field(..., description="Results from browser automation")
