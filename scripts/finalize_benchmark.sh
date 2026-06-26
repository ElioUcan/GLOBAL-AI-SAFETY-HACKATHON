#!/usr/bin/env bash
# Wait for benchmark completion, then regenerate figures + paper from live DB data.
set -euo pipefail
cd "$(dirname "$0")/.."
LOG="${1:-/tmp/bench_all.log}"

if [ -f .env ]; then set -a; source .env; set +a; fi

echo "=== finalize: waiting for BENCHMARK DONE in $LOG ==="
while ! grep -q "BENCHMARK DONE" "$LOG" 2>/dev/null; do
  sleep 30
done
sleep 3

echo "=== finalize: regenerating figures and paper $(date) ==="
python3 scripts/generate_graphical_abstract.py
python3 scripts/generate_result_figures.py
python3 scripts/generate_paper_docx.py

echo "=== FINALIZACION COMPLETA $(date) ==="
docker exec -e PGPASSWORD="${POSTGRES_PASSWORD:-changeme}" slang_postgres \
  psql -U "${POSTGRES_USER:-admin}" -d "${POSTGRES_DB:-slang_bench}" \
  -c 'SELECT target_model, count(*) n, round(avg(jailbreak_success::int)*100,1) asr FROM results WHERE score BETWEEN 1 AND 5 GROUP BY target_model ORDER BY asr DESC;'
