"""Extended results storage with attacker evidence fields."""

from __future__ import annotations

from typing import Any


def store_attack_result(
    conn,
    *,
    jerga_id: int,
    technique: str,
    adversarial_prompt: str,
    target_model: str,
    target_provider: str,
    raw_response: str,
    judge_output: dict[str, Any],
    attacker_model_requested: str,
    attacker_model_used: str,
    is_fallback_triggered: bool,
    slang_integration_score: int,
    prompt_tokens: int,
    completion_tokens: int,
) -> None:
    """Write one benchmark row including attacker audit trail (V2 schema)."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO results (
                jerga_id, attack_technique, generated_prompt,
                target_model, target_provider, response,
                score, jailbreak_success, confidence, severity, judge_reasoning,
                attacker_model_requested, attacker_model_used,
                is_fallback_triggered, slang_integration_score,
                prompt_tokens, completion_tokens
            ) VALUES (
                %(jerga_id)s, %(technique)s, %(adversarial_prompt)s,
                %(target_model)s, %(target_provider)s, %(raw_response)s,
                %(score)s, %(jailbreak_success)s, %(confidence)s, %(severity)s, %(reasoning)s,
                %(attacker_model_requested)s, %(attacker_model_used)s,
                %(is_fallback_triggered)s, %(slang_integration_score)s,
                %(prompt_tokens)s, %(completion_tokens)s
            )
            """,
            {
                "jerga_id": jerga_id,
                "technique": technique,
                "adversarial_prompt": adversarial_prompt,
                "target_model": target_model,
                "target_provider": target_provider,
                "raw_response": raw_response,
                "score": judge_output.get("score", 0),
                "jailbreak_success": judge_output["jailbreak_success"],
                "confidence": judge_output["confidence"],
                "severity": judge_output["severity"],
                "reasoning": judge_output["reasoning"],
                "attacker_model_requested": attacker_model_requested,
                "attacker_model_used": attacker_model_used,
                "is_fallback_triggered": is_fallback_triggered,
                "slang_integration_score": slang_integration_score,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
            },
        )
    conn.commit()


def store_attacker_calibration(
    conn,
    *,
    jerga_id: int | None,
    technique: str,
    term_snapshot: dict[str, Any],
    generation: dict[str, Any],
    sis_score: int,
    sis_reasoning: str,
    calibration_phase: str,
) -> None:
    """Persist a calibration row (attacker-only, no target/judge required)."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO attacker_calibration (
                jerga_id, attack_technique, term, meaning, harm_category, region,
                generated_prompt, attacker_model_requested, attacker_model_used,
                is_fallback_triggered, slang_integration_score, sis_reasoning,
                prompt_tokens, completion_tokens, calibration_phase
            ) VALUES (
                %(jerga_id)s, %(technique)s, %(term)s, %(meaning)s,
                %(harm_category)s, %(region)s, %(generated_prompt)s,
                %(attacker_model_requested)s, %(attacker_model_used)s,
                %(is_fallback_triggered)s, %(sis_score)s, %(sis_reasoning)s,
                %(prompt_tokens)s, %(completion_tokens)s, %(calibration_phase)s
            )
            """,
            {
                "jerga_id": jerga_id,
                "technique": technique,
                "term": term_snapshot["term"],
                "meaning": term_snapshot["meaning"],
                "harm_category": term_snapshot["harm_category"],
                "region": term_snapshot["region"],
                "generated_prompt": generation["adversarial_prompt"],
                "attacker_model_requested": generation["attacker_model_requested"],
                "attacker_model_used": generation["attacker_model_used"],
                "is_fallback_triggered": generation["is_fallback_triggered"],
                "sis_score": sis_score,
                "sis_reasoning": sis_reasoning,
                "prompt_tokens": generation["prompt_tokens"],
                "completion_tokens": generation["completion_tokens"],
                "calibration_phase": calibration_phase,
            },
        )
    conn.commit()
