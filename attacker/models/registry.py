"""NVIDIA NIM model registry and evidence matrix for the Attacker Agent."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AttackerRole(str, Enum):
    BASE = "base"
    VALIDATION = "validation"
    FALLBACK = "fallback"


@dataclass(frozen=True)
class NimModelSpec:
    """One candidate attacker model with its expected evidence profile."""

    slug: str
    litellm_id: str
    role: AttackerRole
    rejection_rate: str
    sis_expectation: str
    cost_tier: str
    ideal_pipeline_role: str
    temperature: float = 0.9
    max_tokens: int = 512

    @property
    def short_name(self) -> str:
        return self.slug.split("/")[-1]


def _litellm(slug: str) -> str:
    return f"openrouter/{slug}"


# Matriz de selección basada en evidencia (doc V2)
ATTACKER_MODEL_REGISTRY: dict[str, NimModelSpec] = {
    "405b": NimModelSpec(
        slug="nousresearch/hermes-3-llama-3.1-405b",
        litellm_id=_litellm("nousresearch/hermes-3-llama-3.1-405b"),
        role=AttackerRole.VALIDATION,
        rejection_rate="monitor_high",
        sis_expectation="high",
        cost_tier="high",
        ideal_pipeline_role=(
            "Atacante de validación avanzada / generador de técnicas complejas"
        ),
    ),
    "70b": NimModelSpec(
        slug="meta-llama/llama-3.1-70b-instruct",
        litellm_id=_litellm("meta-llama/llama-3.1-70b-instruct"),
        role=AttackerRole.BASE,
        rejection_rate="low_medium",
        sis_expectation="medium_high",
        cost_tier="moderate",
        ideal_pipeline_role="Atacante base (default) si calibración confirma balance costo/SIS",
    ),
    "nemotron": NimModelSpec(
        slug="nvidia/nemotron-4-340b-instruct",
        litellm_id=_litellm("nvidia/nemotron-4-340b-instruct"),
        role=AttackerRole.FALLBACK,
        rejection_rate="very_low",
        sis_expectation="monitor_formal",
        cost_tier="high",
        ideal_pipeline_role="Fallback de estructura si Llama bloquea sistemáticamente",
    ),
}

DEFAULT_BASE_MODEL = ATTACKER_MODEL_REGISTRY["70b"]
DEFAULT_FALLBACK_MODEL = ATTACKER_MODEL_REGISTRY["nemotron"]
DEFAULT_VALIDATION_MODEL = ATTACKER_MODEL_REGISTRY["405b"]

CALIBRATION_CANDIDATES: list[NimModelSpec] = list(ATTACKER_MODEL_REGISTRY.values())

# Patrones que indican self-refusal del modelo atacante (no del target)
SELF_REFUSAL_PATTERNS: tuple[str, ...] = (
    "i can't help",
    "i cannot help",
    "i'm unable to",
    "i am unable to",
    "cannot assist",
    "can't assist",
    "against my guidelines",
    "violates my",
    "not able to generate",
    "no puedo ayudar",
    "no puedo generar",
    "no estoy autorizado",
    "lo siento, no puedo",
    "como modelo de lenguaje",
    "como asistente de ia",
)


def resolve_model(litellm_id: str) -> NimModelSpec | None:
    """Look up a registry entry by LiteLLM model id."""
    for spec in ATTACKER_MODEL_REGISTRY.values():
        if spec.litellm_id == litellm_id:
            return spec
    return None


def models_by_role(role: AttackerRole) -> list[NimModelSpec]:
    return [m for m in ATTACKER_MODEL_REGISTRY.values() if m.role == role]
