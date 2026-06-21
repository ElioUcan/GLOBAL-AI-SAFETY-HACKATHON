"""Target Agent — explicit model, no silent fallback."""

from __future__ import annotations

from dataclasses import dataclass

from attacker.gateway.client import GatewayCallResult, GatewayError, chat_completion
from attacker.gateway.config import get_alias_or_none, resolve_gateway_model, resolve_target_alias


@dataclass
class TargetResult:
    raw_response: str
    target_model_requested: str
    target_model_used: str
    target_provider: str
    prompt_tokens: int
    completion_tokens: int
    request_latency_ms: int
    estimated_cost: float | None
    provider_request_id: str | None
    error: str | None = None
    gateway: GatewayCallResult | None = None


def call_target(
    adversarial_prompt: str,
    target: str,
    *,
    provider_mode: str | None = None,
) -> TargetResult:
    """Call target LLM via gateway. Never substitutes another model on failure."""
    alias = resolve_target_alias(target)
    spec = get_alias_or_none(alias)
    gateway_model = resolve_gateway_model(alias, provider_mode=provider_mode) if spec else target
    alias_requested = alias if spec else target

    try:
        gateway = chat_completion(
            alias_requested,
            messages=[{"role": "user", "content": adversarial_prompt}],
            provider_mode=provider_mode,
            spec=spec,
        )
    except GatewayError as exc:
        mode = provider_mode or "nim"
        return TargetResult(
            raw_response="",
            target_model_requested=alias_requested,
            target_model_used=gateway_model,
            target_provider=mode,
            prompt_tokens=0,
            completion_tokens=0,
            request_latency_ms=0,
            estimated_cost=None,
            provider_request_id=None,
            error=str(exc),
        )

    return TargetResult(
        raw_response=gateway.content,
        target_model_requested=alias_requested,
        target_model_used=gateway.model_used,
        target_provider=gateway.provider,
        prompt_tokens=gateway.prompt_tokens,
        completion_tokens=gateway.completion_tokens,
        request_latency_ms=gateway.request_latency_ms,
        estimated_cost=gateway.estimated_cost,
        provider_request_id=gateway.provider_request_id,
        gateway=gateway,
    )
