"""LiteLLM client for NVIDIA NIM."""

from __future__ import annotations

import os
from typing import Any


def completion(model: str, messages: list[dict[str, str]], **kwargs) -> Any:
    """Thin LiteLLM wrapper that injects NVIDIA NIM credentials."""
    import litellm

    return litellm.completion(
        model=model,
        messages=messages,
        **kwargs,
    )


def extract_token_usage(response: Any) -> tuple[int, int]:
    """Return (prompt_tokens, completion_tokens) from a LiteLLM response."""
    usage = getattr(response, "usage", None)
    if usage is None:
        return 0, 0
    prompt = getattr(usage, "prompt_tokens", 0) or 0
    completion = getattr(usage, "completion_tokens", 0) or 0
    return int(prompt), int(completion)
