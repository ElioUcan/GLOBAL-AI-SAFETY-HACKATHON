"""Attacker calibration and model selection (dry-run / live stubs)."""

from __future__ import annotations

from typing import Any

from attacker.models.registry import CALIBRATION_CANDIDATES
from attacker.techniques import VALID_TECHNIQUES, technique_for_iteration


def run_dry_run_calibration(iterations_per_model: int) -> list[dict[str, Any]]:
    plans: list[dict[str, Any]] = []
    for spec in CALIBRATION_CANDIDATES:
        for i in range(1, iterations_per_model + 1):
            plans.append(
                {
                    "model": spec.alias,
                    "role": spec.role.value,
                    "iteration": i,
                    "technique": technique_for_iteration(i),
                }
            )
    return plans


def run_live_attestation(iterations: int, *, persist: bool = True) -> None:
    from attacker.evaluators.sis import evaluate_sis
    from attacker.services.attacker_agent import generate_adversarial_prompt
    from attacker.storage.db import fetch_jerga, get_connection
    from attacker.storage.results import store_attacker_calibration

    conn = get_connection()
    try:
        terms = fetch_jerga(conn, iterations)
        for spec in CALIBRATION_CANDIDATES:
            for i, term in enumerate(terms, start=1):
                technique = technique_for_iteration(i)
                gen = generate_adversarial_prompt(term, technique, force_model=spec.alias)
                sis = evaluate_sis(term, technique, gen.adversarial_prompt, use_heuristic=True)
                if persist:
                    store_attacker_calibration(
                        conn,
                        jerga_id=term["id"],
                        technique=technique,
                        term_snapshot=term,
                        generation={
                            "adversarial_prompt": gen.adversarial_prompt,
                            "attacker_model_requested": gen.attacker_model_requested,
                            "attacker_model_used": gen.attacker_model_used,
                            "is_fallback_triggered": gen.is_fallback_triggered,
                            "prompt_tokens": gen.prompt_tokens,
                            "completion_tokens": gen.completion_tokens,
                        },
                        sis_score=sis.slang_integration_score,
                        sis_reasoning=sis.reasoning,
                        calibration_phase="live",
                    )
    finally:
        conn.close()


def run_model_selection_query() -> list[dict[str, Any]]:
    from attacker.storage.db import get_connection

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT attacker_model_used,
                       AVG(slang_integration_score) AS avg_sis,
                       COUNT(*) AS n
                FROM attacker_calibration
                GROUP BY attacker_model_used
                ORDER BY avg_sis DESC NULLS LAST
                """
            )
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
    finally:
        conn.close()


def print_selection_report(rows: list[dict[str, Any]]) -> None:
    if not rows:
        print("No calibration rows in attacker_calibration.")
        return
    print("=== Model selection (by avg SIS) ===\n")
    for row in rows:
        print(
            f"  {row.get('attacker_model_used', '?')}: "
            f"avg_sis={row.get('avg_sis', 0):.2f} n={row.get('n', 0)}"
        )
