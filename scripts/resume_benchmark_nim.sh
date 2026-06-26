#!/usr/bin/env bash
# Convenience wrapper: resume on NVIDIA NIM (OpenRouter credits exhausted).
set -euo pipefail
cd "$(dirname "$0")/.."
export BENCHMARK_PROVIDER=nvidia_nim
export SIS_EVALUATOR_MODEL="${SIS_EVALUATOR_MODEL:-nvidia_nim/meta/llama-3.1-70b-instruct}"
export NIM_ITER_DELAY="${NIM_ITER_DELAY:-1}"
exec bash scripts/resume_benchmark.sh "$@"
