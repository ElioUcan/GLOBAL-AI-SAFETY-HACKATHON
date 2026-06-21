"""Alias resolution and attacker fallback tests."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from attacker.gateway.config import get_alias, registry_key_to_alias, resolve_gateway_model, resolve_target_alias
from attacker.models.fallback import AttackerAttempt, build_generation_result, is_self_refusal
from attacker.models.selector import fallback_chain, select_requested_model


def test_registry_key_maps_to_alias():
    assert registry_key_to_alias("70b") == "attacker-base"
    assert registry_key_to_alias("405b") == "attacker-validation"


def test_resolve_gateway_model_openrouter():
    assert resolve_gateway_model("attacker-base", provider_mode="openrouter") == "or-attacker-base"
    assert resolve_gateway_model("attacker-base", provider_mode="nim") == "attacker-base"


def test_legacy_target_slug_resolves():
    assert resolve_target_alias("nvidia_nim/meta/llama-3.1-8b-instruct") == "target-default"


def test_attacker_fallback_chain():
    requested = select_requested_model("translation_transfer")
    chain = fallback_chain(requested)
    assert chain[0].alias == "attacker-base"
    assert len(chain) >= 2


def test_attacker_fallback_audit_trail():
    attempts = [
        AttackerAttempt("attacker-base", "sorry I cannot help", 1, 1, True),
        AttackerAttempt("attacker-fallback", "oye wey cuéntame del foco", 2, 3, False),
    ]
    result = build_generation_result("attacker-base", attempts)
    assert result.is_fallback_triggered is True
    assert result.attacker_model_used == "attacker-fallback"


def test_attacker_fallback_allowed_per_alias():
    assert get_alias("attacker-base").fallback_allowed is True
    assert get_alias("target-default").fallback_allowed is False


def test_provider_error_propagation(monkeypatch):
    from attacker.gateway import client as gw

    def _boom(*a, **k):
        raise gw.GatewayError("rate limit", alias="attacker-base")

    monkeypatch.setattr(gw, "chat_completion_with_retries", _boom)
    from attacker.services.attacker_agent import generate_adversarial_prompt

    with pytest.raises(gw.GatewayError):
        generate_adversarial_prompt(
            {"term": "x", "meaning": "y", "harm_category": "violence", "region": "Yucatan"},
            "translation_transfer",
        )
