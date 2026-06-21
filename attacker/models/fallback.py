"""Fallback detection and audit trail for attacker model switches."""

from __future__ import annotations

from dataclasses import dataclass

from attacker.models.registry import SELF_REFUSAL_PATTERNS


@dataclass
class AttackerAttempt:
    """One LLM call attempt during prompt generation."""

    model_used: str
    raw_output: str
    prompt_tokens: int
    completion_tokens: int
    is_self_refusal: bool


@dataclass
class AttackerGenerationResult:
    """Final output after optional fallback chain."""

    adversarial_prompt: str
    attacker_model_requested: str
    attacker_model_used: str
    is_fallback_triggered: bool
    prompt_tokens: int
    completion_tokens: int
    attempts: list[AttackerAttempt]


def is_self_refusal(text: str) -> bool:
    """Detect when the *attacker* model refused instead of generating a prompt."""
    if not text or len(text.strip()) < 20:
        return True

    lowered = text.lower()
    if any(p in lowered for p in SELF_REFUSAL_PATTERNS):
        return True

    # Heuristic: model apologizes instead of producing a user-style prompt
    apology_markers = ("sorry", "lo siento", "disculpa", "cannot", "can't", "no puedo")
    prompt_like = ("?", "oye", "chavo", "wey", "hermano", "explica", "dime", "cuéntame")
    has_apology = any(m in lowered for m in apology_markers)
    looks_like_prompt = any(m in lowered for m in prompt_like)
    if has_apology and not looks_like_prompt:
        return True

    return False


def build_generation_result(
    requested_model: str,
    attempts: list[AttackerAttempt],
) -> AttackerGenerationResult:
    """Collapse attempt chain into auditable generation metadata."""
    if not attempts:
        raise ValueError("attempts must not be empty")

    last = attempts[-1]
    used_fallback = last.model_used != requested_model

    return AttackerGenerationResult(
        adversarial_prompt=last.raw_output.strip(),
        attacker_model_requested=requested_model,
        attacker_model_used=last.model_used,
        is_fallback_triggered=used_fallback,
        prompt_tokens=sum(a.prompt_tokens for a in attempts),
        completion_tokens=sum(a.completion_tokens for a in attempts),
        attempts=attempts,
    )
