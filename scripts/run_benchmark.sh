#!/usr/bin/env bash
# Sequential benchmark runner across all target models (round-robin techniques).
set -euo pipefail
cd "$(dirname "$0")/.."

export PYTHONUNBUFFERED=1

MODELS=(
  "openrouter/meta-llama/llama-3.1-8b-instruct"
  "openrouter/mistralai/ministral-8b-2512"
  "openrouter/google/gemma-3-12b-it"
  "openrouter/google/gemini-2.5-flash"
)
LIMIT="${1:-70}"

if docker ps --format '{{.Names}}' 2>/dev/null | grep -qx slang_n8n; then
  echo "ERROR: slang_n8n is running — it writes to results in parallel and corrupts counts."
  echo "       Run: docker stop slang_n8n"
  exit 1
fi

echo "=== BENCHMARK START $(date) — limit=$LIMIT per model × ${#MODELS[@]} targets ==="
for m in "${MODELS[@]}"; do
  echo ""
  echo "########## TARGET: $m ##########"
  python3 -m attacker.main run --target "$m" --limit "$LIMIT"
done
echo ""
echo "=== BENCHMARK DONE $(date) ==="
