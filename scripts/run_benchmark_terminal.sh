#!/usr/bin/env bash
# Run the full benchmark in the foreground (use in a dedicated terminal tab).
# Prerequisites: docker stop slang_n8n  (n8n corrupts results if running)
set -euo pipefail
cd "$(dirname "$0")/.."

if docker ps --format '{{.Names}}' 2>/dev/null | grep -qx slang_n8n; then
  echo "Stopping n8n first (writes to results in parallel)..."
  docker stop slang_n8n
fi

export PYTHONUNBUFFERED=1
: > /tmp/bench_all.log

echo "Starting benchmark 4 models × 70 — log: /tmp/bench_all.log"
bash scripts/run_benchmark.sh 70 2>&1 | tee /tmp/bench_all.log

echo ""
echo "Regenerating figures and paper..."
bash scripts/finalize_benchmark.sh /tmp/bench_all.log
