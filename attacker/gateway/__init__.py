"""LiteLLM Proxy gateway — central LLM access layer."""

from attacker.gateway.client import GatewayCallResult, GatewayError, chat_completion, health_check
from attacker.gateway.config import ModelAliasSpec, get_alias, load_models_config, resolve_gateway_model

__all__ = [
    "GatewayCallResult",
    "GatewayError",
    "ModelAliasSpec",
    "chat_completion",
    "get_alias",
    "health_check",
    "load_models_config",
    "resolve_gateway_model",
]
