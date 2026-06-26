#!/usr/bin/env bash
# Resume benchmark — 3 targets, rotating 3 attackers + 3 judges per iteration.
# OpenRouter by default; set BENCHMARK_PROVIDER=nvidia_nim for NVIDIA NIM slugs.
set -euo pipefail
cd "$(dirname "$0")/.."

export PYTHONUNBUFFERED=1
LIMIT="${1:-45}"
PROVIDER="${BENCHMARK_PROVIDER:-openrouter}"

if docker ps --format '{{.Names}}' 2>/dev/null | grep -qx slang_n8n; then
  echo "Stopping n8n (corrupts results)..."
  docker stop slang_n8n
fi

if [ "$PROVIDER" = "nvidia_nim" ]; then
  MODELS=(
    "nvidia_nim/meta/llama-3.1-8b-instruct"
    "nvidia_nim/meta/llama-3.2-3b-instruct"
    "nvidia_nim/meta/llama-3.3-70b-instruct"
  )
else
  MODELS=(
    "openrouter/meta-llama/llama-3.1-8b-instruct"
    "openrouter/mistralai/ministral-8b-2512"
    "openrouter/google/gemma-3-12b-it"
  )
fi

echo "=== RESUME BENCHMARK $(date) — provider=$PROVIDER limit=$LIMIT rotate-lineup=ON ==="
bash scripts/benchmark_status.sh "$LIMIT" "$PROVIDER"
echo ""

for m in "${MODELS[@]}"; do
  if [ "$PROVIDER" = "nvidia_nim" ]; then
    slug="${m#nvidia_nim/}"
  else
    slug="${m#openrouter/}"
  fi
  N=$(python3 - <<PY
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
  if [ "$N" -ge "$LIMIT" ]; then
    echo "SKIP $slug ($N/$LIMIT already done)"
    continue
  fi
  REMAIN=$((LIMIT - N))
  echo ""
  echo "########## TARGET: $m ($N done, running $REMAIN more) ##########"
  export BENCHMARK_PROVIDER="$PROVIDER"
  python3 -m attacker.main run --target "$m" --limit "$REMAIN" --rotate-lineup
done

echo ""
echo "=== BENCHMARK DONE $(date) ===" | tee -a /tmp/bench_all.log
echo "=== Regenerating figures + paper notes ==="
python3 scripts/generate_graficas_resultados.py
python3 scripts/generate_graphical_abstract.py
python3 scripts/generate_result_figures.py
echo "=== FINALIZACION COMPLETA $(date) ==="
