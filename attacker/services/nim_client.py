"""LiteLLM client — delegates to the central gateway (keeps LiteLLM in the stack)."""

from __future__ import annotations

from typing import Any

from attacker.gateway.client import GatewayCallResult, chat_completion as gateway_chat


def completion(model: str, messages: list[dict[str, str]], **kwargs) -> Any:
    """Backward-compatible LiteLLM-shaped wrapper over the gateway.

    ``model`` may be a stable alias (e.g. ``attacker-base``) or a legacy slug.
    """
    alias = model
    if "/" in model and not model.startswith("or-"):
        from attacker.gateway.config import resolve_target_alias

        alias = resolve_target_alias(model)

    temperature = kwargs.pop("temperature", None)
    max_tokens = kwargs.pop("max_tokens", None)
    timeout = kwargs.pop("timeout", None)
    provider_mode = kwargs.pop("provider_mode", None)

    result: GatewayCallResult = gateway_chat(
        alias,
        messages,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
        provider_mode=provider_mode,
    )
    return result.raw_response


def extract_token_usage(response: Any) -> tuple[int, int]:
    """Return (prompt_tokens, completion_tokens) from a gateway or LiteLLM response."""
    if isinstance(response, GatewayCallResult):
        return response.prompt_tokens, response.completion_tokens
    usage = getattr(response, "usage", None)
    if usage is None:
        return 0, 0
    prompt = getattr(usage, "prompt_tokens", 0) or 0
    completion = getattr(usage, "completion_tokens", 0) or 0
    return int(prompt), int(completion)
