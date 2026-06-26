# Nota metodológica — Fase B (NIM) · n8n / operadores

**Fecha:** 2026-06-22 · **Estado:** Fase B en curso vía **CLI Python**, n8n **detenido** durante recolección.

## Por qué NIM y no OpenRouter

| Motivo | Detalle |
|--------|---------|
| **Costo** | OpenRouter: saldo negativo → HTTP 402 en todos los modelos de pago |
| **Tiempo** | Entrega hackathon ~6:00; imposible completar 280 runs en OpenRouter |
| **Ajuste de muestra** | **45 runs × 3 targets = 135** (antes 70 × 3 = 210) |

## Qué NO cambió (paridad n8n ↔ CLI)

- Corpus `jerga` (HarmBench-ES × jerga mexicana/yucateca)
- 7 técnicas de ataque (incl. `pair_refine` solo en CLI)
- Regex pre-filter → Judge 1–5 → Storage PostgreSQL
- SIS evaluator · rotación 3 attackers + 3 judges (`--rotate-lineup`)

## Fase B — NVIDIA NIM

- **Env:** `BENCHMARK_PROVIDER=nvidia_nim`, `NVIDIA_API_KEY`
- **Targets:** `meta/llama-3.1-8b-instruct`, `meta/llama-3.2-3b-instruct`, `meta/llama-3.3-70b-instruct`
- **Comando:** `bash scripts/resume_benchmark_nim.sh 45`
- **Columna DB:** `target_provider = 'nvidia_nim'`

## Fase A — OpenRouter (suplementaria)

- **111 filas preservadas** (`target_provider = 'openrouter'`)
- Llama 8B 70/70 · Ministral 41/70 · Gemma/Gemini no corridos

## n8n — reglas durante benchmark

1. **`docker stop slang_n8n`** antes de CLI — n8n escribe en `results` en paralelo y duplica filas.
2. No reconfigurar n8n a NIM mid-run; el workflow V0.1.4 sigue documentado para OpenRouter.
3. Grafana lee las mismas vistas ASR; filtrar por `target_provider` si se comparan fases.

## Paper

Texto listo en `PAPER_NOTAS.md` §4.6 y frases ejemplo EN/ES.
