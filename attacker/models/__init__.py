"""Model registry exports."""

from attacker.models.fallback import (
    AttackerAttempt,
    AttackerGenerationResult,
    build_generation_result,
    is_self_refusal,
)
from attacker.models.registry import (
    ATTACKER_MODEL_REGISTRY,
    CALIBRATION_CANDIDATES,
    DEFAULT_BASE_MODEL,
    DEFAULT_FALLBACK_MODEL,
    DEFAULT_VALIDATION_MODEL,
    AttackerRole,
    NimModelSpec,
)
from attacker.models.selector import fallback_chain, select_requested_model

__all__ = [
    "ATTACKER_MODEL_REGISTRY",
    "AttackerAttempt",
    "AttackerGenerationResult",
    "AttackerRole",
    "CALIBRATION_CANDIDATES",
    "DEFAULT_BASE_MODEL",
    "DEFAULT_FALLBACK_MODEL",
    "DEFAULT_VALIDATION_MODEL",
    "NimModelSpec",
    "build_generation_result",
    "fallback_chain",
    "is_self_refusal",
    "select_requested_model",
]
