"""Security helpers: optional API-key auth and shared rate limiter."""

from __future__ import annotations

import os

from fastapi import Header, HTTPException, status
from slowapi import Limiter
from slowapi.util import get_remote_address

# Shared limiter keyed by client IP. Used to throttle expensive LLM routes.
limiter = Limiter(key_func=get_remote_address)

# Default per-client limit for the LLM chat endpoint. Override via env.
CHAT_RATE_LIMIT = os.getenv("CHAT_RATE_LIMIT", "20/minute")


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """
    Enforce an API key when API_KEY is configured.

    If API_KEY is unset (e.g. local dev), the check is skipped so the app
    stays usable. In production, set API_KEY to require the X-API-Key header.
    """
    expected = os.getenv("API_KEY")
    if not expected:
        return
    if not x_api_key or x_api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
        )
