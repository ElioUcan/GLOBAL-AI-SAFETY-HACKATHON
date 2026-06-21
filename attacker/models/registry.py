"""NVIDIA NIM model registry and evidence matrix for the Attacker Agent."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from attacker.gateway.config import registry_key_to_alias


class AttackerRole(str, Enum):
    BASE = "base"
    VALIDATION = "validation"
    FALLBACK = "fallback"


@dataclass(frozen=True)
class NimModelSpec:
    """One candidate attacker model with its expected evidence profile."""

    slug: str
    alias: str
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


def _spec(
    key: str,
    slug: str,
    role: AttackerRole,
    rejection_rate: str,
    sis_expectation: str,
    cost_tier: str,
    ideal_pipeline_role: str,
) -> NimModelSpec:
    alias = registry_key_to_alias(key)
    return NimModelSpec(
        slug=slug,
        alias=alias,
        litellm_id=alias,
        role=role,
        rejection_rate=rejection_rate,
        sis_expectation=sis_expectation,
        cost_tier=cost_tier,
        ideal_pipeline_role=ideal_pipeline_role,
    )


ATTACKER_MODEL_REGISTRY: dict[str, NimModelSpec] = {
    "405b": _spec(
        "405b",
        "meta/llama-3.1-405b-instruct",
        AttackerRole.VALIDATION,
        "monitor_high",
        "high",
        "high",
        "Atacante de validación avanzada / generador de técnicas complejas",
    ),
    "70b": _spec(
        "70b",
        "meta/llama-3.1-70b-instruct",
        AttackerRole.BASE,
        "low_medium",
        "medium_high",
        "moderate",
        "Atacante base (default) si calibración confirma balance costo/SIS",
    ),
    "nemotron": _spec(
        "nemotron",
        "nvidia/nemotron-4-340b-instruct",
        AttackerRole.FALLBACK,
        "very_low",
        "monitor_formal",
        "high",
        "Fallback de estructura si Llama bloquea sistemáticamente",
    ),
}

DEFAULT_BASE_MODEL = ATTACKER_MODEL_REGISTRY["70b"]
DEFAULT_FALLBACK_MODEL = ATTACKER_MODEL_REGISTRY["nemotron"]
DEFAULT_VALIDATION_MODEL = ATTACKER_MODEL_REGISTRY["405b"]

CALIBRATION_CANDIDATES: list[NimModelSpec] = list(ATTACKER_MODEL_REGISTRY.values())

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


def resolve_model(identifier: str) -> NimModelSpec | None:
    """Look up a registry entry by key, alias, or legacy litellm id."""
    if identifier in ATTACKER_MODEL_REGISTRY:
        return ATTACKER_MODEL_REGISTRY[identifier]
    for spec in ATTACKER_MODEL_REGISTRY.values():
        if spec.alias == identifier or spec.litellm_id == identifier or spec.slug == identifier:
            return spec
    return None


def models_by_role(role: AttackerRole) -> list[NimModelSpec]:
    return [m for m in ATTACKER_MODEL_REGISTRY.values() if m.role == role]
