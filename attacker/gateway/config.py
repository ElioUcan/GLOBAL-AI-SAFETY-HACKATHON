"""Load declarative model aliases from config/models.yaml."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODELS_PATH = _ROOT / "config" / "models.yaml"


@dataclass(frozen=True)
class ModelAliasSpec:
    alias: str
    pipeline_role: str
    gateway_model: str
    gateway_model_openrouter: str
    temperature: float
    max_tokens: int
    timeout: int
    retries: int
    fallback_allowed: bool
    description: str = ""


def _parse_alias(alias: str, data: dict[str, Any]) -> ModelAliasSpec:
    return ModelAliasSpec(
        alias=alias,
        pipeline_role=str(data["pipeline_role"]),
        gateway_model=str(data["gateway_model"]),
        gateway_model_openrouter=str(data.get("gateway_model_openrouter", data["gateway_model"])),
        temperature=float(data.get("temperature", 0.7)),
        max_tokens=int(data.get("max_tokens", 512)),
        timeout=int(data.get("timeout", 120)),
        retries=int(data.get("retries", 0)),
        fallback_allowed=bool(data.get("fallback_allowed", False)),
        description=str(data.get("description", "")),
    )


@lru_cache(maxsize=1)
def load_models_config(path: str | None = None) -> dict[str, Any]:
    cfg_path = Path(path) if path else DEFAULT_MODELS_PATH
    if not cfg_path.is_file():
        raise FileNotFoundError(f"models config not found: {cfg_path}")
    with cfg_path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def get_alias(alias: str, *, config: dict[str, Any] | None = None) -> ModelAliasSpec:
    cfg = config or load_models_config()
    aliases = cfg.get("aliases") or {}
    if alias not in aliases:
        raise KeyError(f"Unknown model alias: {alias}")
    return _parse_alias(alias, aliases[alias])


def resolve_gateway_model(alias: str, *, provider_mode: str | None = None) -> str:
    """Map stable alias to LiteLLM Proxy model_name."""
    spec = get_alias(alias)
    mode = (provider_mode or os.getenv("LITELLM_PROVIDER_MODE", "nim")).lower()
    if mode == "openrouter":
        return spec.gateway_model_openrouter
    return spec.gateway_model


def resolve_target_alias(target: str) -> str:
    """Resolve legacy --target slug or alias to a stable target alias."""
    cfg = load_models_config()
    mapping = cfg.get("target_aliases") or {}
    if target in mapping:
        return mapping[target]
    if target.startswith("or-"):
        return target
    # Raw slug not in mapping — use as custom target via target-default pattern
    return target if get_alias_or_none(target) else "target-default"


def get_alias_or_none(alias: str) -> ModelAliasSpec | None:
    try:
        return get_alias(alias)
    except KeyError:
        return None


def registry_key_to_alias(key: str) -> str:
    cfg = load_models_config()
    mapping = cfg.get("registry_mapping") or {}
    return mapping.get(key, "attacker-base")


def regex_decides_result() -> bool:
    env = os.getenv("REGEX_DECIDES_RESULT")
    if env is not None:
        return env.lower() in ("1", "true", "yes")
    cfg = load_models_config()
    regex_cfg = cfg.get("regex") or {}
    return bool(regex_cfg.get("decides_result", False))
