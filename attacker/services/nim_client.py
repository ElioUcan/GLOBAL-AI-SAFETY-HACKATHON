"""LiteLLM client with retry/backoff on transient errors.

Supports a dual-API strategy: NVIDIA NIM (attacker, judge, SIS, and the
open-weight targets) plus OpenRouter (highly-aligned "hard" targets such as
Claude and GPT-4o). Credentials are resolved per model-slug prefix so a single
client can talk to both providers without forcing one provider's base URL onto
the other.
"""

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


def _provider_credentials(model: str) -> dict[str, Any]:
    """Resolve api_key / api_base for a model slug (dual-API routing).

    - ``nvidia_nim/*``  → NVIDIA NIM key + base (attacker, judge, SIS, NIM targets)
    - ``openrouter/*``  → OpenRouter key (+ optional base override); LiteLLM
      defaults the base to ``https://openrouter.ai/api/v1``.
    - anything else     → no overrides; let LiteLLM resolve from its own env vars.

    Forcing NVIDIA's base URL onto an OpenRouter slug (the previous behavior) made
    "hard" targets like Claude/GPT-4o unreachable, so routing is now prefix-based.
    """
    if model.startswith("openrouter/"):
        creds: dict[str, Any] = {}
        key = os.getenv("OPENROUTER_API_KEY")
        if key:
            creds["api_key"] = key
        base = os.getenv("OPENROUTER_API_BASE")
        if base:
            creds["api_base"] = base
        return creds

    if model.startswith("nvidia_nim/"):
        return {
            "api_key": os.getenv("NVIDIA_API_KEY"),
            "api_base": os.getenv("NVIDIA_API_BASE", "https://integrate.api.nvidia.com/v1"),
        }

    return {}


def completion(model: str, messages: list[dict[str, str]], **kwargs) -> Any:
    """Thin LiteLLM wrapper that injects per-provider credentials and retries.

    Credentials are routed by model-slug prefix (see ``_provider_credentials``)
    so NVIDIA NIM and OpenRouter targets share one code path. Transient failures
    (HTTP 429 / 5xx / connection / timeout) are retried up to ``NIM_MAX_RETRIES``
    times with exponential backoff + jitter, honoring a ``Retry-After`` header
    when the server sends one.
    """
    import litellm

    retryable = _retryable_exceptions()
    creds = _provider_credentials(model)

    attempt = 0
    while True:
        try:
            return litellm.completion(
                model=model,
                messages=messages,
                **creds,
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
