"""LiteLLM client for NVIDIA NIM with retry/backoff on transient errors."""

from __future__ import annotations

import os
import random
import sys
import time
from typing import Any

# Default retry policy (override via env).
_MAX_RETRIES = int(os.getenv("NIM_MAX_RETRIES", "5"))
_BACKOFF_BASE = float(os.getenv("NIM_BACKOFF_BASE", "2.0"))  # seconds
_BACKOFF_CAP = float(os.getenv("NIM_BACKOFF_CAP", "60.0"))   # seconds


def _retryable_exceptions() -> tuple[type[BaseException], ...]:
    """Transient LiteLLM errors worth retrying (rate limit, 5xx, network)."""
    import litellm

    names = (
        "RateLimitError",
        "Timeout",
        "APIConnectionError",
        "InternalServerError",
        "ServiceUnavailableError",
    )
    exc = tuple(
        getattr(litellm, name) for name in names if hasattr(litellm, name)
    )
    return exc or (Exception,)


def _retry_after_seconds(exc: BaseException) -> float | None:
    """Honor a server-provided Retry-After header if available."""
    response = getattr(exc, "response", None)
    headers = getattr(response, "headers", None)
    if not headers:
        return None
    value = headers.get("retry-after") or headers.get("Retry-After")
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _sleep_for(exc: BaseException, attempt: int) -> float:
    """Compute the delay before the next attempt (1-indexed attempt number)."""
    retry_after = _retry_after_seconds(exc)
    if retry_after is not None:
        return retry_after
    # Exponential backoff with full jitter, capped.
    backoff = min(_BACKOFF_BASE * (2 ** (attempt - 1)), _BACKOFF_CAP)
    return backoff + random.uniform(0, 1)


def completion(model: str, messages: list[dict[str, str]], **kwargs) -> Any:
    """Thin LiteLLM wrapper that injects NVIDIA NIM credentials and retries.

    Transient failures (HTTP 429 / 5xx / connection / timeout) are retried up to
    ``NIM_MAX_RETRIES`` times with exponential backoff + jitter, honoring a
    ``Retry-After`` header when the server sends one.
    """
    import litellm

    retryable = _retryable_exceptions()
    api_key = os.getenv("NVIDIA_API_KEY")
    api_base = os.getenv("NVIDIA_API_BASE", "https://integrate.api.nvidia.com/v1")

    attempt = 0
    while True:
        try:
            return litellm.completion(
                model=model,
                messages=messages,
                api_key=api_key,
                api_base=api_base,
                **kwargs,
            )
        except retryable as exc:
            attempt += 1
            if attempt > _MAX_RETRIES:
                raise
            delay = _sleep_for(exc, attempt)
            print(
                f"[nim_client] {type(exc).__name__} on {model} — retry "
                f"{attempt}/{_MAX_RETRIES} in {delay:.1f}s",
                file=sys.stderr,
            )
            time.sleep(delay)


def extract_token_usage(response: Any) -> tuple[int, int]:
    """Return (prompt_tokens, completion_tokens) from a LiteLLM response."""
    usage = getattr(response, "usage", None)
    if usage is None:
        return 0, 0
    prompt = getattr(usage, "prompt_tokens", 0) or 0
    completion = getattr(usage, "completion_tokens", 0) or 0
    return int(prompt), int(completion)
