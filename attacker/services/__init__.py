"""Attacker services."""

from attacker.services.attacker_agent import generate_adversarial_prompt
from attacker.services.nim_client import completion, extract_token_usage

__all__ = [
    "completion",
    "extract_token_usage",
    "generate_adversarial_prompt",
]
