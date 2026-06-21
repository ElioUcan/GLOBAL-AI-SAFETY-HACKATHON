"""LiteLLM Proxy client — all LLM calls route through the central gateway."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any

from attacker.gateway.config import ModelAliasSpec, get_alias, resolve_gateway_model


class GatewayError(Exception):
    """Raised when the gateway returns an error (no silent target fallback)."""

    def __init__(self, message: str, *, alias: str | None = None, provider: str | None = None):
        super().__init__(message)
        self.alias = alias
        self.provider = provider


@dataclass
class GatewayCallResult:
    content: str
    alias_requested: str
    model_used: str
    provider: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    request_latency_ms: int = 0
    estimated_cost: float | None = None
    provider_request_id: str | None = None
    raw_response: Any = field(default=None, repr=False)


def _provider_mode() -> str:
    return os.getenv("LITELLM_PROVIDER_MODE", "nim").lower()


def _gateway_base_url() -> str:
    base = os.getenv("LITELLM_BASE_URL", "http://localhost:4000")
    return base.rstrip("/")


def _gateway_api_key() -> str | None:
    return os.getenv("LITELLM_MASTER_KEY") or os.getenv("LITELLM_API_KEY")


def _extract_request_id(response: Any) -> str | None:
    rid = getattr(response, "id", None)
    if rid:
        return str(rid)
    hidden = getattr(response, "_hidden_params", None) or {}
    if isinstance(hidden, dict):
        return hidden.get("request_id") or hidden.get("litellm_call_id")
    return None


def _extract_cost(response: Any) -> float | None:
    hidden = getattr(response, "_hidden_params", None) or {}
    if isinstance(hidden, dict):
        cost = hidden.get("response_cost")
        if cost is not None:
            try:
                return float(cost)
            except (TypeError, ValueError):
                pass
    return None


def chat_completion(
    alias: str,
    messages: list[dict[str, str]],
    *,
    temperature: float | None = None,
    max_tokens: int | None = None,
    timeout: int | None = None,
    provider_mode: str | None = None,
    spec: ModelAliasSpec | None = None,
) -> GatewayCallResult:
    """Call LiteLLM Proxy using a stable alias."""
    import litellm

    spec = spec or get_alias(alias)
    mode = provider_mode or _provider_mode()
    gateway_model = resolve_gateway_model(alias, provider_mode=mode)
    api_base = _gateway_base_url()
    api_key = _gateway_api_key()

    if not api_key:
        raise GatewayError(
            "LITELLM_MASTER_KEY is not set",
            alias=alias,
            provider=mode,
        )

    started = time.perf_counter()
    try:
        response = litellm.completion(
            model=gateway_model,
            messages=messages,
            api_base=f"{api_base}/v1",
            api_key=api_key,
            custom_llm_provider="openai",
            temperature=spec.temperature if temperature is None else temperature,
            max_tokens=spec.max_tokens if max_tokens is None else max_tokens,
            timeout=spec.timeout if timeout is None else timeout,
        )
    except Exception as exc:
        raise GatewayError(str(exc), alias=alias, provider=mode) from exc

    latency_ms = int((time.perf_counter() - started) * 1000)
    usage = getattr(response, "usage", None)
    prompt_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
    completion_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
    content = ""
    choices = getattr(response, "choices", None) or []
    if choices:
        message = getattr(choices[0], "message", None)
        content = getattr(message, "content", None) or ""

    return GatewayCallResult(
        content=content.strip(),
        alias_requested=alias,
        model_used=gateway_model,
        provider=mode,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        request_latency_ms=latency_ms,
        estimated_cost=_extract_cost(response),
        provider_request_id=_extract_request_id(response),
        raw_response=response,
    )


def chat_completion_with_retries(
    alias: str,
    messages: list[dict[str, str]],
    *,
    provider_mode: str | None = None,
    **kwargs: Any,
) -> GatewayCallResult:
    spec = get_alias(alias)
    last_error: GatewayError | None = None
    attempts = max(1, spec.retries + 1)
    for _ in range(attempts):
        try:
            return chat_completion(alias, messages, provider_mode=provider_mode, spec=spec, **kwargs)
        except GatewayError as exc:
            last_error = exc
    assert last_error is not None
    raise last_error


def health_check(*, provider_mode: str | None = None) -> dict[str, Any]:
    """Ping LiteLLM Proxy /health and report configured provider mode."""
    import urllib.error
    import urllib.request

    base = _gateway_base_url()
    status: dict[str, Any] = {
        "gateway_url": base,
        "provider_mode": provider_mode or _provider_mode(),
        "master_key_set": bool(_gateway_api_key()),
    }
    try:
        req = urllib.request.Request(f"{base}/health", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            status["healthy"] = resp.status == 200
            status["status_code"] = resp.status
    except urllib.error.URLError as exc:
        status["healthy"] = False
        status["error"] = str(exc)
    return status


def list_providers() -> dict[str, Any]:
    """Return provider availability based on env keys (no secrets exposed)."""
    mode = _provider_mode()
    return {
        "active_mode": mode,
        "nim_configured": bool(os.getenv("NVIDIA_API_KEY")),
        "openrouter_configured": bool(os.getenv("OPENROUTER_API_KEY")),
        "gateway_url": _gateway_base_url(),
        "aliases": list((load_models_config_safe() or {}).get("aliases", {}).keys()),
    }


def load_models_config_safe() -> dict[str, Any] | None:
    try:
        from attacker.gateway.config import load_models_config

        return load_models_config()
    except FileNotFoundError:
        return None
