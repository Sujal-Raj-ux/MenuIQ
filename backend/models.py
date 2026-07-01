"""Pydantic schemas shared by the AI layer and FastAPI (Phase 4)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

QuadrantLabel = Literal["Star", "Plowhorse", "Puzzle", "Dog"]
RecommendationCategory = Literal[
    "placement", "combo", "promotion", "pricing", "retire"
]


class MenuItemAnalysis(BaseModel):
    """One row of the menu-engineering matrix."""

    item_id: int
    name: str
    category: str
    units_sold: int
    margin: float
    quadrant: QuadrantLabel


class AssociationPair(BaseModel):
    """A directed market-basket association between two items."""

    antecedent_name: str
    consequent_name: str
    support: float
    confidence: float
    lift: float


class Recommendation(BaseModel):
    """A single prioritized menu action derived from pre-computed analytics."""

    priority: int = Field(..., ge=1, le=10, description="1 = highest priority")
    title: str
    recommendation: str = Field(
        ...,
        description="Plain-English action; must only restate supplied facts.",
    )
    supporting_facts: list[str] = Field(
        ...,
        description="Verbatim metrics copied from the analytics payload.",
    )
    related_items: list[str]
    category: RecommendationCategory


class RecommendationsOutput(BaseModel):
    """Structured output from the recommendation chain."""

    executive_summary: str
    recommendations: list[Recommendation]


class ChatResponse(BaseModel):
    """Response from the conversational agent."""

    answer: str
    structured_data: dict | None = Field(
        default=None,
        description="Optional compact data the frontend can render (e.g. quadrant).",
    )


class ChatRequest(BaseModel):
    """Body for POST /chat."""

    question: str = Field(..., min_length=1, max_length=2000)
    session_id: str = Field(
        default="default",
        description="Conversation key for multi-turn memory.",
    )


class MenuAnalysisResponse(BaseModel):
    """GET /menu-analysis — deterministic matrix plus LLM recommendations."""

    items: list[MenuItemAnalysis]
    popularity_threshold: float
    margin_threshold: float
    executive_summary: str
    recommendations: list[Recommendation]


class MenuMatrixResponse(BaseModel):
    """GET /menu-matrix — deterministic menu-engineering data only (no LLM)."""

    items: list[MenuItemAnalysis]
    popularity_threshold: float
    margin_threshold: float


class AssociationsResponse(BaseModel):
    """GET /associations — top market-basket pairs by lift."""

    pairs: list[AssociationPair]


class UploadResponse(BaseModel):
    """POST /upload — summary of an ingested transaction dataset."""

    session_id: str = Field(
        ...,
        description="Pass this as session_id on analytics/chat calls to use this dataset.",
    )
    orders: int
    line_items: int
    distinct_items: int
    warnings: list[str] = Field(default_factory=list)
