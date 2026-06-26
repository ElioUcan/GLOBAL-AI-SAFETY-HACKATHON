#!/usr/bin/env bash
# Show benchmark progress — 3 target models per provider lineup.
set -euo pipefail
cd "$(dirname "$0")/.."

LIMIT="${1:-45}"
PROVIDER="${2:-${BENCHMARK_PROVIDER:-openrouter}}"

if [ "$PROVIDER" = "nvidia_nim" ]; then
  MODELS=(
    "meta/llama-3.1-8b-instruct"
    "meta/llama-3.2-3b-instruct"
    "meta/llama-3.3-70b-instruct"
  )
else
  MODELS=(
    "meta-llama/llama-3.1-8b-instruct"
    "mistralai/ministral-8b-2512"
    "google/gemma-3-12b-it"
  )
fi

echo "=== BENCHMARK STATUS (provider=$PROVIDER, target: $LIMIT per model) ==="
echo ""

TOTAL=0
DONE_MODELS=0
for slug in "${MODELS[@]}"; do
  N=$(python3 - <<PY 2>/dev/null || echo 0
import os, psycopg2
from dotenv import load_dotenv
load_dotenv(".env")
conn = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST","localhost"),
    port=os.getenv("POSTGRES_PORT","5432"),
    user=os.getenv("POSTGRES_USER","admin"),
    password=os.getenv("POSTGRES_PASSWORD","changeme"),
    dbname=os.getenv("POSTGRES_DB","slang_bench"),
)
cur = conn.cursor()
cur.execute(
    "SELECT count(*) FROM results WHERE target_model=%s AND score BETWEEN 1 AND 5",
    ("$slug",),
)
print(cur.fetchone()[0])
conn.close()
PY
)
  TOTAL=$((TOTAL + N))
  if [ "$N" -ge "$LIMIT" ]; then
    STATUS="✓ COMPLETO"
    DONE_MODELS=$((DONE_MODELS + 1))
  elif [ "$N" -gt 0 ]; then
    STATUS="→ EN CURSO ($N/$LIMIT)"
  else
    STATUS="○ pendiente"
  fi
  echo "  $slug  $N/$LIMIT  $STATUS"
done

echo ""
echo "  TOTAL FILAS EN DB (this lineup): $TOTAL / $((LIMIT * ${#MODELS[@]}))"
echo ""

python3 - <<'PY' 2>/dev/null || true
import os, psycopg2
from dotenv import load_dotenv
load_dotenv(".env")
conn = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST","localhost"),
    port=os.getenv("POSTGRES_PORT","5432"),
    user=os.getenv("POSTGRES_USER","admin"),
    password=os.getenv("POSTGRES_PASSWORD","changeme"),
    dbname=os.getenv("POSTGRES_DB","slang_bench"),
)
cur = conn.cursor()
cur.execute("""
    SELECT count(*) n, round(avg(jailbreak_success::numeric)*100,2) asr,
           round(avg(slang_integration_score)::numeric,2) sis
    FROM results WHERE score BETWEEN 1 AND 5
""")
n, asr, sis = cur.fetchone()
print(f"  GLOBAL (all providers): N={n}  ASR={asr}%  mean SIS={sis}")
conn.close()
PY

if grep -q "402\|requires more credits\|Insufficient credits" /tmp/bench_all.log 2>/dev/null; then
  echo ""
  echo "⚠️  OpenRouter credit errors in /tmp/bench_all.log — try:"
  echo "     BENCHMARK_PROVIDER=nvidia_nim bash scripts/resume_benchmark.sh"
fi

if grep -q "BENCHMARK DONE" /tmp/bench_all.log 2>/dev/null; then
  echo "✓ Benchmark finished. Regenerate: python3 scripts/generate_graficas_resultados.py"
fi
