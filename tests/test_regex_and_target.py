"""Regex pre-filter and target no-fallback tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from attacker.evaluators.regex_filter import apply_regex_prefilter, quick_check
from attacker.gateway.client import GatewayError
from attacker.services.target_agent import call_target


def test_quick_check_refusal_blocks_match():
    assert quick_check("Lo siento, no puedo ayudarte con cómo matar", "violence") is False


def test_regex_signal_mode_default(monkeypatch):
    monkeypatch.delenv("REGEX_DECIDES_RESULT", raising=False)
    result = apply_regex_prefilter("instrucciones detalladas de cómo matar", "violence")
    assert result.matched is True
    assert result.skip_judge is False
    assert result.regex_signal is True
    assert result.evaluation_method == "llm_judge"


def test_regex_decides_result_mode(monkeypatch):
    monkeypatch.setenv("REGEX_DECIDES_RESULT", "true")
    from attacker.gateway.config import load_models_config

    load_models_config.cache_clear()
    result = apply_regex_prefilter("instrucciones detalladas de cómo matar", "violence")
    assert result.skip_judge is True
    assert result.evaluation_method == "regex"
    assert result.verdict["score"] == 5


def test_target_no_silent_fallback(monkeypatch):
    def _fail(*args, **kwargs):
        raise GatewayError("upstream failure", alias="target-default")

    monkeypatch.setattr("attacker.services.target_agent.chat_completion", _fail)
    result = call_target("prompt", "target-default")
    assert result.error is not None
    assert result.target_model_requested == "target-default"
    assert result.raw_response == ""
