#!/usr/bin/env bash
# Neutral Spanish control arm — split for parallel runners.
# Usage:
#   bash scripts/run_neutral_control.sh a   # rows 0–262   → log /tmp/neutral_a.log
#   bash scripts/run_neutral_control.sh b   # rows 263–524 → log /tmp/neutral_b.log
#
# Override target (run different models in parallel):
#   TARGET=nvidia_nim/meta/llama-3.2-3b-instruct bash scripts/run_neutral_control.sh b
set -euo pipefail
cd "$(dirname "$0")/.."

export PYTHONUNBUFFERED=1
export BENCHMARK_PROVIDER="${BENCHMARK_PROVIDER:-nvidia_nim}"
export SIS_EVALUATOR_MODEL="${SIS_EVALUATOR_MODEL:-nvidia_nim/meta/llama-3.1-70b-instruct}"
export NIM_ITER_DELAY="${NIM_ITER_DELAY:-1}"

PERSON="${1:-a}"
TOTAL="${NEUTRAL_TOTAL:-525}"
TARGET="${TARGET:-nvidia_nim/meta/llama-3.1-8b-instruct}"

docker stop slang_n8n 2>/dev/null || true

if [ "$PERSON" = "a" ]; then
  OFFSET=0
  LIMIT=$(( (TOTAL + 1) / 2 ))   # 263 when TOTAL=525
  LOG=/tmp/neutral_person_a.log
elif [ "$PERSON" = "b" ]; then
  OFFSET=$(( (TOTAL + 1) / 2 ))
  LIMIT=$(( TOTAL / 2 ))         # 262 when TOTAL=525
  LOG=/tmp/neutral_person_b.log
else
  echo "Usage: $0 a|b" >&2
  exit 1
fi

echo "=== NEUTRAL CONTROL person=$PERSON offset=$OFFSET limit=$LIMIT target=$TARGET ===" | tee -a "$LOG"
python3 -m attacker.main run \
  --corpus neutral \
  --deterministic \
  --target "$TARGET" \
  --offset "$OFFSET" \
  --limit "$LIMIT" \
  2>&1 | tee -a "$LOG"

echo "=== NEUTRAL DONE person=$PERSON $(date) ===" | tee -a "$LOG"
