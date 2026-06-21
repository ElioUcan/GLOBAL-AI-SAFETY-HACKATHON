"""Evidence-based model selection for the Attacker Agent."""

from __future__ import annotations

import os

from attacker.models.registry import (
    DEFAULT_BASE_MODEL,
    DEFAULT_FALLBACK_MODEL,
    DEFAULT_VALIDATION_MODEL,
    AttackerRole,
    NimModelSpec,
    models_by_role,
)
from attacker.techniques import is_complex


def model_from_env(key: str, default: NimModelSpec) -> NimModelSpec:
    """Resolve a LiteLLM id from env, falling back to registry default."""
    from attacker.models.registry import resolve_model

    litellm_id = os.getenv(key, default.litellm_id)
    return resolve_model(litellm_id) or default


def select_requested_model(
    technique: str,
    *,
    force_model: str | None = None,
) -> NimModelSpec:
    """Pick the model that *should* run for this iteration.

    Selection logic (evidence-first, not size-first):
    - Explicit ``force_model`` wins (calibration / CLI override).
    - Complex techniques prefer the validation (405B) model.
    - Everything else uses the calibrated base (70B default).
    """
    if force_model:
        from attacker.models.registry import resolve_model

        resolved = resolve_model(force_model)
        if resolved:
            return resolved
        # Allow raw LiteLLM slug not in registry (forward compat)
        return NimModelSpec(
            slug=force_model.split("/", 1)[-1],
            litellm_id=force_model,
            role=AttackerRole.BASE,
            rejection_rate="unknown",
            sis_expectation="unknown",
            cost_tier="unknown",
            ideal_pipeline_role="CLI override",
        )

    if is_complex(technique):
        return model_from_env("ATTACKER_VALIDATION_MODEL", DEFAULT_VALIDATION_MODEL)

    return model_from_env("ATTACKER_DEFAULT_MODEL", DEFAULT_BASE_MODEL)


def fallback_chain(requested: NimModelSpec) -> list[NimModelSpec]:
    """Ordered list of models to try when the primary self-refuses."""
    chain: list[NimModelSpec] = [requested]
    fallback = model_from_env("ATTACKER_FALLBACK_MODEL", DEFAULT_FALLBACK_MODEL)

    if fallback.litellm_id != requested.litellm_id:
        chain.append(fallback)

    # Never fall back to validation model from base — different purpose
    for base in models_by_role(AttackerRole.BASE):
        if base.litellm_id not in {m.litellm_id for m in chain}:
            if requested.role == AttackerRole.VALIDATION:
                chain.append(base)
            break

    return chain
