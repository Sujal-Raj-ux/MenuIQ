"""Conversational agent with curated tools and session memory."""

from __future__ import annotations

import re
from typing import Any

from ai.llm import get_llm
from langchain.agents import create_agent
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import InMemorySaver

from ai.tools import ALL_TOOLS
from models import ChatResponse

SYSTEM_PROMPT = """You are MenuIQ, an AI assistant for restaurant menu optimization.

You answer questions about menu performance, item pairings, and whether to
promote, bundle, or retire items.

CRITICAL RULES:
1. NEVER compute metrics yourself (units sold, lift, margins, percentages).
2. ALWAYS call the provided tools to fetch pre-computed analytics.
3. Base every number in your answer on tool output — quote tool results directly.
4. If asked about a specific item, call get_item_stats and/or get_item_associations.
5. For menu-wide questions, call get_menu_matrix first.
6. Be concise and actionable. If data suggests an item is a Dog but has high lift
   as an add-on, explain that nuance instead of recommending a blind cut.

"""


class MenuIQAgent:
    """
    Tool-calling agent with per-session conversation memory.

    Uses LangGraph's InMemorySaver so each session_id (thread_id) retains
    prior turns for multi-turn chat.
    """

    def __init__(self) -> None:
        self._checkpointer = InMemorySaver()
        self._graph = create_agent(
            model=get_llm(),
            tools=ALL_TOOLS,
            system_prompt=SYSTEM_PROMPT,
            checkpointer=self._checkpointer,
        )

    def ask(self, question: str, session_id: str = "default") -> ChatResponse:
        """
        Answer a free-text question using curated analytics tools.

        Args:
            question: User question in plain English.
            session_id: Conversation key for multi-turn memory.
        """
        result = self._graph.invoke(
            {"messages": [{"role": "user", "content": question}]},
            config={"configurable": {"thread_id": session_id}},
        )
        answer = _extract_answer(result["messages"])
        structured = _extract_structured_data(answer)
        return ChatResponse(answer=answer, structured_data=structured)


def clear_session(session_id: str) -> None:
    """
    Placeholder for session reset.

    InMemorySaver persists by thread_id for the process lifetime; Phase 4 can
    swap in a store-backed checkpointer if durable reset is required.
    """
    # LangGraph InMemorySaver has no per-thread delete API; new thread_ids
    # effectively start fresh. Documented for the FastAPI layer.
    _ = session_id


def _extract_answer(messages: list[Any]) -> str:
    """Return the final assistant message text from the agent message list."""
    for message in reversed(messages):
        if isinstance(message, AIMessage) and message.content:
            content = message.content
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                parts = [
                    block.get("text", "")
                    for block in content
                    if isinstance(block, dict) and block.get("type") == "text"
                ]
                return "".join(parts)
    return ""


def _extract_structured_data(answer: str) -> dict[str, Any] | None:
    """
    Pull compact structured hints from the agent answer for the frontend.

    Detects quadrant mentions and item names so Phase 5 can optionally highlight them.
    """
    quadrants = ("Star", "Plowhorse", "Puzzle", "Dog")
    items = (
        "Classic Burger",
        "Truffle Fries",
        "Lobster Roll",
        "Onion Rings",
        "Veggie Burger",
        "Soda",
        "Milkshake",
    )

    mentioned_items = [name for name in items if name.lower() in answer.lower()]
    mentioned_quadrants = [q for q in quadrants if q in answer]

    if not mentioned_items and not mentioned_quadrants:
        return None

    data: dict[str, Any] = {}
    if mentioned_items:
        data["items"] = mentioned_items
    if mentioned_quadrants:
        data["quadrants"] = mentioned_quadrants

    lift_match = re.search(r"lift[=:\s]+(\d+\.?\d*)", answer, re.IGNORECASE)
    if lift_match:
        data["lift"] = float(lift_match.group(1))

    return data
