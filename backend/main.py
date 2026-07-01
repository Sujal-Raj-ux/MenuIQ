"""FastAPI application — REST layer over analytics and AI pipelines."""

from __future__ import annotations

import os
from typing import Annotated

from dotenv import load_dotenv
from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

load_dotenv()

from ai.agent import MenuIQAgent
from ai.context import (
    AnalyticsContext,
    analytics_context,
    reset_active_context,
    set_active_context,
)
from ai.recommendations import generate_recommendations
from ingest import IngestError, parse_transactions
from models import (
    AssociationPair,
    AssociationsResponse,
    ChatRequest,
    ChatResponse,
    MenuAnalysisResponse,
    MenuItemAnalysis,
    MenuMatrixResponse,
    UploadResponse,
)
from security import CHAT_RATE_LIMIT, limiter, require_api_key
from session_store import session_store

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB

app = FastAPI(
    title="MenuIQ API",
    description="Menu optimization analytics and AI recommendations",
    version="0.1.0",
)

# Rate limiting (slowapi): register limiter + 429 handler + middleware.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Allowed frontend origins. Defaults to local dev; set CORS_ORIGINS in prod
# to a comma-separated list of your real frontend domains.
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174,http://localhost:3000",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in CORS_ORIGINS if origin.strip()],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key"],
)

_agent: MenuIQAgent | None = None


def _require_groq_key() -> None:
    if not os.getenv("GROQ_API_KEY"):
        raise HTTPException(
            status_code=503,
            detail="GROQ_API_KEY is not configured. Add it to your .env file.",
        )


def _get_agent() -> MenuIQAgent:
    global _agent
    _require_groq_key()
    if _agent is None:
        _agent = MenuIQAgent()
    return _agent


def _resolve_context(session_id: str | None) -> AnalyticsContext:
    """Return the uploaded-dataset context for session_id, else the demo dataset."""
    ctx = session_store.get(session_id)
    return ctx if ctx is not None else analytics_context


def _matrix_to_items(matrix_df) -> list[MenuItemAnalysis]:
    return [
        MenuItemAnalysis(
            item_id=int(row["item_id"]),
            name=str(row["name"]),
            category=str(row["category"]),
            units_sold=int(row["units_sold"]),
            margin=float(row["margin"]),
            quadrant=row["quadrant"],
        )
        for _, row in matrix_df.iterrows()
    ]


def _associations_to_pairs(associations_df, limit: int) -> list[AssociationPair]:
    pairs: list[AssociationPair] = []
    for _, row in associations_df.head(limit).iterrows():
        pairs.append(
            AssociationPair(
                antecedent_name=str(row["antecedent_name"]),
                consequent_name=str(row["consequent_name"]),
                support=float(row["support"]),
                confidence=float(row["confidence"]),
                lift=float(row["lift"]),
            )
        )
    return pairs


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness check (no OpenAI key required)."""
    return {"status": "ok"}


@app.post(
    "/upload",
    response_model=UploadResponse,
    dependencies=[Depends(require_api_key)],
)
async def upload(
    file: UploadFile = File(...),
    cost_pct: Annotated[float | None, Form()] = None,
) -> UploadResponse:
    """
    Ingest a user's transaction file (CSV/Excel) into an isolated analysis session.

    The file is parsed and normalized into the same canonical tables used for the
    demo data, then the same Phase 2 analytics run on it. Pass the returned
    session_id to the analytics and chat endpoints to view results for this data.

    Profitability needs a food_cost or margin column in the file; if neither
    exists, supply cost_pct (an assumed food-cost percentage of price). That is
    your stated assumption — metrics are still computed in Python, never by the LLM.
    """
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit.",
        )
    try:
        result = parse_transactions(
            raw, file.filename or "upload.csv", cost_pct=cost_pct
        )
        session_id = session_store.create(result)
    except IngestError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return UploadResponse(
        session_id=session_id,
        orders=result.orders,
        line_items=result.line_items,
        distinct_items=result.distinct_items,
        warnings=result.warnings,
    )


@app.get(
    "/menu-matrix",
    response_model=MenuMatrixResponse,
    dependencies=[Depends(require_api_key)],
)
def menu_matrix(
    session_id: Annotated[str | None, Query()] = None,
) -> MenuMatrixResponse:
    """Menu-engineering matrix only (deterministic; no LLM). Used by the dashboard chart."""
    matrix_df = _resolve_context(session_id).matrix_df
    return MenuMatrixResponse(
        items=_matrix_to_items(matrix_df),
        popularity_threshold=float(matrix_df.iloc[0]["popularity_threshold"]),
        margin_threshold=float(matrix_df.iloc[0]["margin_threshold"]),
    )


@app.get(
    "/menu-analysis",
    response_model=MenuAnalysisResponse,
    dependencies=[Depends(require_api_key)],
)
def menu_analysis(
    session_id: Annotated[str | None, Query()] = None,
) -> MenuAnalysisResponse:
    """
    Deterministic dashboard pipeline: menu-engineering matrix + LLM recommendations.

    All metrics are computed in Python/Pandas first; the LLM only phrases actions.
    """
    _require_groq_key()
    ctx = _resolve_context(session_id)
    matrix_df = ctx.matrix_df
    recs = generate_recommendations(context=ctx)

    return MenuAnalysisResponse(
        items=_matrix_to_items(matrix_df),
        popularity_threshold=float(matrix_df.iloc[0]["popularity_threshold"]),
        margin_threshold=float(matrix_df.iloc[0]["margin_threshold"]),
        executive_summary=recs.executive_summary,
        recommendations=sorted(recs.recommendations, key=lambda r: r.priority),
    )


@app.get(
    "/associations",
    response_model=AssociationsResponse,
    dependencies=[Depends(require_api_key)],
)
def associations(
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    session_id: Annotated[str | None, Query()] = None,
) -> AssociationsResponse:
    """Top market-basket pairs by lift (deterministic; no LLM)."""
    pairs = _associations_to_pairs(_resolve_context(session_id).associations_df, limit)
    return AssociationsResponse(pairs=pairs)


@app.post(
    "/chat",
    response_model=ChatResponse,
    dependencies=[Depends(require_api_key)],
)
@limiter.limit(CHAT_RATE_LIMIT)
def chat(request: Request, body: ChatRequest) -> ChatResponse:
    """
    Agentic chat pipeline: LLM selects curated analytics tools to answer the question.

    If session_id matches an uploaded dataset, the agent answers over that data;
    otherwise it uses the demo dataset. Rate-limited per client IP.
    """
    agent = _get_agent()
    token = set_active_context(_resolve_context(body.session_id))
    try:
        return agent.ask(body.question, session_id=body.session_id)
    finally:
        reset_active_context(token)
