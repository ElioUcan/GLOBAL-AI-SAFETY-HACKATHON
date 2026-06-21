"""Evidence-based model selection for the Attacker Agent."""

from __future__ import annotations

import os

from attacker.gateway.config import get_alias
from attacker.models.registry import (
    DEFAULT_BASE_MODEL,
    DEFAULT_FALLBACK_MODEL,
    DEFAULT_VALIDATION_MODEL,
    AttackerRole,
    NimModelSpec,
    models_by_role,
    resolve_model,
)
from attacker.techniques import is_complex


def _alias_spec(alias: str) -> NimModelSpec:
    get_alias(alias)  # validate exists
    resolved = resolve_model(alias)
    if resolved:
        return resolved
    return NimModelSpec(
        slug=alias,
        alias=alias,
        litellm_id=alias,
        role=AttackerRole.BASE,
        rejection_rate="unknown",
        sis_expectation="unknown",
        cost_tier="unknown",
        ideal_pipeline_role="alias override",
    )


def model_from_env(key: str, default: NimModelSpec) -> NimModelSpec:
    """Resolve an alias from env, falling back to registry default."""
    alias = os.getenv(key, default.alias)
    return resolve_model(alias) or _alias_spec(alias)


def select_requested_model(
    technique: str,
    *,
    force_model: str | None = None,
) -> NimModelSpec:
    """Pick the model alias that *should* run for this iteration."""
    if force_model:
        resolved = resolve_model(force_model)
        if resolved:
            return resolved
        return _alias_spec(force_model)

    if is_complex(technique):
        return model_from_env("ATTACKER_VALIDATION_ALIAS", DEFAULT_VALIDATION_MODEL)

    return model_from_env("ATTACKER_DEFAULT_ALIAS", DEFAULT_BASE_MODEL)


def fallback_chain(requested: NimModelSpec) -> list[NimModelSpec]:
    """Ordered list of model aliases to try when the primary self-refuses."""
    chain: list[NimModelSpec] = [requested]
    fallback = model_from_env("ATTACKER_FALLBACK_ALIAS", DEFAULT_FALLBACK_MODEL)

    if fallback.alias != requested.alias:
        chain.append(fallback)

    for base in models_by_role(AttackerRole.BASE):
        if base.alias not in {m.alias for m in chain}:
            if requested.role == AttackerRole.VALIDATION:
                chain.append(base)
            break

    return chain
