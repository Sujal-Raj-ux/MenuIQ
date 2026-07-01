"""Shared Groq LLM client for the AI layer."""

from __future__ import annotations

import os

from langchain_groq import ChatGroq

DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"


def get_llm() -> ChatGroq:
    """
    Return a Groq chat model for recommendations and the agent.

    """
    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError(
            "GROQ_API_KEY is not set. Add it to your .env file to run the AI layer."
        )
    model = os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL)
    return ChatGroq(model=model, temperature=0)
