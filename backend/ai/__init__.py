"""MenuIQ AI layer: recommendation chain and conversational agent."""

from ai.agent import MenuIQAgent, clear_session
from ai.recommendations import generate_recommendations

__all__ = ["MenuIQAgent", "clear_session", "generate_recommendations"]

# Lazy public API — import submodules directly in tests to avoid loading
# the agent (and OpenAI client) when only tools are needed.
