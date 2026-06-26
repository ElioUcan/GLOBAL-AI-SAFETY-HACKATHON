"""Three-model lineups per pipeline role (Attacker, Target, Judge).

Slugs are LiteLLM ids (openrouter/... or nvidia_nim/...). Override any list via env
comma-separated vars: TARGET_LINEUP, ATTACKER_LINEUP, JUDGE_LINEUP.
"""

from __future__ import annotations

import os


def _split_env(key: str, default: tuple[str, ...]) -> tuple[str, ...]:
    raw = os.getenv(key, "")
    if not raw.strip():
        return default
    return tuple(s.strip() for s in raw.split(",") if s.strip())


# Default: OpenRouter (requires OPENROUTER_API_KEY). Set PROVIDER=nvidia_nim to use NIM slugs.
_PROVIDER = os.getenv("BENCHMARK_PROVIDER", "openrouter")


def _p(slug: str) -> str:
    return f"{_PROVIDER}/{slug}" if _PROVIDER != "openrouter" else f"openrouter/{slug}"


DEFAULT_TARGETS: tuple[str, ...] = (
    "meta-llama/llama-3.1-8b-instruct",
    "mistralai/ministral-8b-2512",
    "google/gemma-3-12b-it",
)

DEFAULT_ATTACKERS: tuple[str, ...] = (
    "meta-llama/llama-3.1-70b-instruct",
    "nousresearch/hermes-3-llama-3.1-405b",
    "google/gemma-3-27b-it",
)

DEFAULT_JUDGES: tuple[str, ...] = (
    "meta-llama/llama-3.1-70b-instruct",
    "google/gemini-2.5-flash",
    "mistralai/mistral-large-2512",
)

# NIM fallback lineups (no openrouter/ prefix — full nvidia_nim/ ids)
NIM_TARGETS: tuple[str, ...] = (
    "nvidia_nim/meta/llama-3.1-8b-instruct",
    "nvidia_nim/meta/llama-3.2-3b-instruct",
    "nvidia_nim/meta/llama-3.3-70b-instruct",
)

NIM_ATTACKERS: tuple[str, ...] = (
    "nvidia_nim/meta/llama-3.1-70b-instruct",
    "nvidia_nim/meta/llama-3.3-70b-instruct",
    "nvidia_nim/meta/llama-3.1-8b-instruct",
)

NIM_JUDGES: tuple[str, ...] = (
    "nvidia_nim/meta/llama-3.1-70b-instruct",
    "nvidia_nim/meta/llama-3.3-70b-instruct",
    "nvidia_nim/meta/llama-3.2-3b-instruct",
)


def targets() -> tuple[str, ...]:
    if _PROVIDER == "nvidia_nim":
        return _split_env("TARGET_LINEUP", NIM_TARGETS)
    return tuple(_p(s) for s in _split_env("TARGET_LINEUP", DEFAULT_TARGETS))


def attackers() -> tuple[str, ...]:
    if _PROVIDER == "nvidia_nim":
        return _split_env("ATTACKER_LINEUP", NIM_ATTACKERS)
    return tuple(_p(s) for s in _split_env("ATTACKER_LINEUP", DEFAULT_ATTACKERS))


def judges() -> tuple[str, ...]:
    if _PROVIDER == "nvidia_nim":
        return _split_env("JUDGE_LINEUP", NIM_JUDGES)
    return tuple(_p(s) for s in _split_env("JUDGE_LINEUP", DEFAULT_JUDGES))


def for_iteration(items: tuple[str, ...], iteration: int) -> str:
    if iteration < 1:
        raise ValueError("iteration must be >= 1")
    return items[(iteration - 1) % len(items)]
