"""LangChain recommendation chain — LLM phrases pre-computed analytics only."""

from __future__ import annotations

from ai.llm import get_llm
from langchain_core.prompts import ChatPromptTemplate

from ai.context import AnalyticsContext, analytics_context
from ai.formatters import format_matrix_facts, format_top_associations
from models import RecommendationsOutput

SYSTEM_PROMPT = """You are a restaurant menu consultant for MenuIQ.

You receive PRE-COMPUTED analytics facts from a deterministic Python/Pandas pipeline.
You must NOT invent, estimate, or recalculate any numbers.

Rules:
1. Every supporting_fact must copy a metric verbatim from the facts block.
2. Recommendations must cite only items and numbers present in the facts.
3. Prioritize actions by business impact: Stars (protect), Puzzles (promote),
   Plowhorses (margin-up or bundle), Dogs (cut/rework unless strong attach lift).
4. Highlight high-lift combo opportunities from the association data.
5. Return 3–6 recommendations sorted by priority (1 = highest).
"""

USER_PROMPT = """Using ONLY the facts below, produce prioritized menu recommendations.

=== MENU ENGINEERING FACTS ===
{matrix_facts}

=== TOP ASSOCIATION FACTS ===
{association_facts}

Return a single valid JSON object (no markdown, no extra prose) with this exact shape:
{{
  "executive_summary": "<one or two sentence overview>",
  "recommendations": [
    {{
      "priority": <integer, 1 = highest priority>,
      "title": "<short title>",
      "recommendation": "<plain-English action>",
      "supporting_facts": ["<metric copied verbatim from the facts>"],
      "related_items": ["<item name>"],
      "category": "<one of: placement, combo, promotion, pricing, retire>"
    }}
  ]
}}

Rules for the JSON:
- "priority" MUST be a JSON integer (e.g. 1), never a string like "1".
- Return 3 to 6 recommendations, sorted by priority ascending.
- Do not compute new metrics; copy numbers verbatim from the facts above."""

_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        ("user", USER_PROMPT),
    ]
)


def generate_recommendations(
    context: AnalyticsContext | None = None,
) -> RecommendationsOutput:
    """
    Run menu-engineering + market-basket analytics, then phrase recommendations.

    All quantitative analysis happens before the LLM call; the model only
    packages the supplied facts into prioritized plain-English actions.
    """
    ctx = context or analytics_context
    matrix_facts = format_matrix_facts(ctx.matrix_df)
    association_facts = format_top_associations(ctx.associations_df, limit=10)

    # Use Groq JSON mode (not function_calling): Groq's strict tool-schema
    # validation rejects values like priority="1", whereas JSON mode lets
    # Pydantic parse and coerce the response client-side.
    llm = get_llm().with_structured_output(RecommendationsOutput, method="json_mode")
    chain = _prompt | llm
    return chain.invoke(
        {
            "matrix_facts": matrix_facts,
            "association_facts": association_facts,
        }
    )
