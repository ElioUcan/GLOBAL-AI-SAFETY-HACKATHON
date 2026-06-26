#!/usr/bin/env bash
# Top-up slang runs to match neutral corpus size (default 525).
# Uses deterministic ORDER BY id + partitioned offsets so each NIM target
# covers a disjoint slice of the same jerga rows as the neutral control arm.
#
# Usage:
#   bash scripts/run_slang_balance_nim.sh          # launch 3 parallel jobs
#   bash scripts/run_slang_balance_nim.sh status # print counts
#   bash scripts/run_slang_balance_nim.sh 8b|3b|70b  # run one shard only (foreground)
set -euo pipefail
cd "$(dirname "$0")/.."

export PYTHONUNBUFFERED=1
export BENCHMARK_PROVIDER=nvidia_nim
export SIS_EVALUATOR_MODEL="${SIS_EVALUATOR_MODEL:-nvidia_nim/meta/llama-3.1-70b-instruct}"
export NIM_ITER_DELAY="${NIM_ITER_DELAY:-1}"

TARGET_TOTAL="${SLANG_TARGET_TOTAL:-525}"
CORPUS_TOTAL="${NEUTRAL_TOTAL:-525}"
CHUNK=$(( (CORPUS_TOTAL + 2) / 3 ))   # 175 when CORPUS_TOTAL=525

M8B="nvidia_nim/meta/llama-3.1-8b-instruct"
M3B="nvidia_nim/meta/llama-3.2-3b-instruct"
M70B="nvidia_nim/meta/llama-3.3-70b-instruct"

docker stop slang_n8n 2>/dev/null || true

count_slang() {
  python3 - <<'PY'
import os, psycopg2
from dotenv import load_dotenv
load_dotenv(".env")
conn = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST", "localhost"),
    port=os.getenv("POSTGRES_PORT", "5432"),
    user=os.getenv("POSTGRES_USER", "admin"),
    password=os.getenv("POSTGRES_PASSWORD", "changeme"),
    dbname=os.getenv("POSTGRES_DB", "slang_bench"),
)
cur = conn.cursor()
cur.execute(
    "SELECT count(*) FROM results WHERE corpus_condition='slang' AND score BETWEEN 1 AND 5"
)
print(cur.fetchone()[0])
conn.close()
PY
}

count_neutral() {
  python3 - <<'PY'
import os, psycopg2
from dotenv import load_dotenv
load_dotenv(".env")
conn = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST", "localhost"),
    port=os.getenv("POSTGRES_PORT", "5432"),
    user=os.getenv("POSTGRES_USER", "admin"),
    password=os.getenv("POSTGRES_PASSWORD", "changeme"),
    dbname=os.getenv("POSTGRES_DB", "slang_bench"),
)
cur = conn.cursor()
cur.execute(
    "SELECT count(*) FROM results WHERE corpus_condition='neutral' AND score BETWEEN 1 AND 5"
)
print(cur.fetchone()[0])
conn.close()
PY
}

need_more() {
  local current="$1"
  echo $(( TARGET_TOTAL - current ))
}

run_shard() {
  local name="$1" model="$2" offset="$3" limit="$4" log="$5"
  if [ "$limit" -le 0 ]; then
    echo "SKIP $name (limit=$limit)"
    return 0
  fi
  echo "=== SLANG BALANCE $name offset=$offset limit=$limit target=$model ===" | tee -a "$log"
  python3 -m attacker.main run \
    --corpus slang \
    --deterministic \
    --target "$model" \
    --offset "$offset" \
    --limit "$limit" \
    --rotate-lineup \
    2>&1 | tee -a "$log"
  echo "=== SLANG BALANCE DONE $name $(date) ===" | tee -a "$log"
}

plan_limits() {
  local need="$1"
  # Three disjoint slices of the 525-row deterministic corpus (175 each).
  # Scale down proportionally if we need fewer than 525 new rows total.
  if [ "$need" -ge "$CORPUS_TOTAL" ]; then
    L8=$CHUNK
    L3=$CHUNK
    L70=$(( CORPUS_TOTAL - CHUNK - CHUNK ))
  else
    L8=$(( (need * CHUNK + CORPUS_TOTAL - 1) / CORPUS_TOTAL ))
    L3=$(( (need * CHUNK + CORPUS_TOTAL - 1) / CORPUS_TOTAL ))
    L70=$(( need - L8 - L3 ))
    if [ "$L70" -lt 0 ]; then L70=0; fi
  fi
  echo "$L8 $L3 $L70"
}

if [ "${1:-}" = "status" ]; then
  echo "Slang scored:   $(count_slang) / $TARGET_TOTAL"
  echo "Neutral scored: $(count_neutral) / $CORPUS_TOTAL"
  exit 0
fi

CURRENT=$(count_slang)
NEED=$(need_more "$CURRENT")
if [ "$NEED" -le 0 ]; then
  echo "Slang already at or above $TARGET_TOTAL ($CURRENT). Nothing to do."
  exit 0
fi

read -r L8 L3 L70 <<< "$(plan_limits "$NEED")"
O8=0
O3=$CHUNK
O70=$(( CHUNK * 2 ))

echo "=== SLANG BALANCE PLAN $(date) ==="
echo "Current slang=$CURRENT  need=$NEED  target=$TARGET_TOTAL"
echo "Shards: 8B offset=$O8 limit=$L8 | 3B offset=$O3 limit=$L3 | 70B offset=$O70 limit=$L70"

case "${1:-all}" in
  8b)
    run_shard "8B" "$M8B" "$O8" "$L8" "/tmp/slang_balance_8b.log"
    ;;
  3b)
    run_shard "3B" "$M3B" "$O3" "$L3" "/tmp/slang_balance_3b.log"
    ;;
  70b)
    run_shard "70B" "$M70B" "$O70" "$L70" "/tmp/slang_balance_70b.log"
    ;;
  all)
    nohup bash "$0" 8b >> /tmp/slang_balance_8b.log 2>&1 &
    echo "Started 8B PID=$!"
    sleep 3
    nohup bash "$0" 3b >> /tmp/slang_balance_3b.log 2>&1 &
    echo "Started 3B PID=$!"
    sleep 3
    nohup bash "$0" 70b >> /tmp/slang_balance_70b.log 2>&1 &
    echo "Started 70B PID=$!"
    echo "Logs: /tmp/slang_balance_{8b,3b,70b}.log"
    ;;
  *)
    echo "Usage: $0 [all|8b|3b|70b|status]" >&2
    exit 2
    ;;
esac
