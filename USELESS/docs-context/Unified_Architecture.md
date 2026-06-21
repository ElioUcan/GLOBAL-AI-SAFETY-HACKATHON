# Unified Architecture (V2 Attacker + 1-5 Scoring)

This document explains the unified architecture deployed in the latest iteration of the benchmark. It merges the telemetry systems of the V2 Attacker with Fernando's 1-5 scoring logic for the Judge.

## 1. Database Schema unification
The `01-schema.sql` file was updated to be the "Ultimate Schema". It now holds:
- **Judge Metrics (from Fernando):** `score` (1-5) and `harm_detected` columns. The `jailbreak_success` boolean is automatically derived from the score (true if score >= 4).
- **Attacker Metrics (from V2 Attacker):** `slang_integration_score`, `attacker_model_requested`, `attacker_model_used`, `is_fallback_triggered`, `prompt_tokens`, and `completion_tokens`.
- **Attacker Calibration:** A new table `attacker_calibration` tracks the specific calibration phase metrics.

## 2. V2 Attacker Patching
The V2 Python Attacker (`attacker/main.py` and `attacker/storage/results.py`) was successfully patched. It now:
1. Loads the master judge prompt directly from `docs/context/master_judge_prompt.md`.
2. Emits a `score` field (from 1 to 5) during the Judge JSON parsing phase.
3. Automatically populates `score: 5` when the regex pre-filter matches and skips the Judge.
4. Correctly populates the PostgreSQL database inserting both the judge metrics and the telemetry metrics simultaneously.

## 3. Grafana Dashboard (11 Panels)
The `jailbreak_metrics.json` dashboard was expanded to include 11 panels to provide an Enterprise-grade view of the benchmark metrics.
- The top row now features 4 identical KPI panels: Total Attack Attempts, Overall Jailbreak Success Rate, Average Judge Confidence, and the newly added **Average Slang Integration Score (SIS)**.
- We added live tracking tables like "Most Dangerous Slang Terms" and "Recent Successful Jailbreaks".
- The dashboard is perfectly aligned horizontally and vertically, occupying a symmetric 24x28 grid.
