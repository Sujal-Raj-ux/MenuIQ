#!/usr/bin/env python3
"""
Demo Phase 3 AI layer (requires GROQ_API_KEY in .env).

Usage:
  python scripts/demo_ai.py recommendations
  python scripts/demo_ai.py chat "Should I cut the onion rings?"
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from ai.agent import MenuIQAgent
from ai.recommendations import generate_recommendations
from ai.tools import _get_menu_matrix


def main() -> None:
    parser = argparse.ArgumentParser(description="Demo MenuIQ AI layer")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("tools", help="Print tool output (no API key needed)")
    sub.add_parser("recommendations", help="Run recommendation chain")
    chat_parser = sub.add_parser("chat", help="Ask the agent a question")
    chat_parser.add_argument("question", type=str)

    args = parser.parse_args()

    if args.command == "tools":
        print(_get_menu_matrix())
        return

    if args.command == "recommendations":
        result = generate_recommendations()
        print(json.dumps(result.model_dump(), indent=2))
        return

    if args.command == "chat":
        agent = MenuIQAgent()
        response = agent.ask(args.question, session_id="demo")
        print(response.answer)
        if response.structured_data:
            print("\nStructured data:", json.dumps(response.structured_data, indent=2))
        return


if __name__ == "__main__":
    main()
