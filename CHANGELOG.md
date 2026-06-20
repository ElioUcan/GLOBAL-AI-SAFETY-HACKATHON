# Changelog

All notable changes to the Yucatan Slang Jailbreak Benchmark are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [V0.1.0]

### Added
- `n8nWorkflow.json` — full n8n workflow implementing the AGENTS.md pipeline:
  Attack Config → Fetch Jerga (Postgres) → Attacker Agent (Llama 405B @ 0.9) →
  Target LLM (NVIDIA NIM HTTP @ 0.7) → Regex pre-filter → Judge Agent
  (Llama 70B @ 0.0, structured JSON output) → Store Result (Postgres INSERT).
  Includes sticky notes for setup and PAIR loop guidance. No credentials are
  embedded in the export — bind Postgres and NVIDIA credentials in the n8n UI
  after import.
- Docker infrastructure: `compose.yml` orchestrating three services — PostgreSQL,
  n8n, and Grafana — on a shared `slang_net` bridge network.
- Per-service Dockerfiles under `docker/`:
  - `docker/postgres/Dockerfile` — `postgres:16` with a first-boot init hook
    (`init/` mounted into `/docker-entrypoint-initdb.d/`).
  - `docker/n8n/Dockerfile` — `n8nio/n8n`, using its first-party PostgreSQL node.
  - `docker/grafana/Dockerfile` — Grafana using its built-in, signed PostgreSQL
    datasource (no community plugin required).
- Grafana provisioning: PostgreSQL datasource and dashboard provider wired via
  `docker/grafana/provisioning/`.
- `.env.example` template documenting all configuration variables.

### Changed
- Storage backend is PostgreSQL: the `postgres` service replaces MongoDB, and the
  n8n / Grafana services connect over `POSTGRES_*` env vars instead of `MONGO_URL`.
- Restricted all LLM calls (attacker, targets, judge) to NVIDIA NIM only.
  Removed Gemini, Anthropic, Groq, and local Ollama configuration.
- Trimmed the `AGENTS.md` Supported Targets table to the four NVIDIA NIM models
  and updated the "Adding a New Target LLM" guide accordingly.
- Grafana dashboard mount now points at the `./grafana` directory instead of a
  single (possibly missing) JSON file.
- Replaced the placeholder `n8nWorkflow.json` skeleton (empty agent prompts,
  wrong node types, regex after Judge, DeepSeek/OpenAI target, chat-memory instead
  of DB fetch) with a workflow aligned to `AGENTS.md`.

### Known gaps

#### n8n workflow (not yet implemented)

- **Credentials** — Postgres and NVIDIA API credentials must be configured
  manually in n8n after import (`Fetch Jerga`, `Store Result`, Attacker LLM,
  Judge LLM). Target LLM reads `$env.NVIDIA_API_KEY` from the container env.
- **PAIR loop (`pair_refine`)** — multi-turn attacker→target→judge iteration
  (max 5 rounds, early stop at confidence ≥ 0.8) is documented via sticky note
  only; needs a sub-workflow or Loop node.
- **Batch coverage** — AGENTS.md calls for 3–5 prompts per (term, technique)
  combination; the workflow runs a single attack per execution.
- **Technique rotation** — Attack Config defaults to `translation_transfer`; no
  loop over the other six techniques (`semantic_obfuscation`, `crescendo`,
  `codeswitching`, `roleplay_wrap`, `manyshot_slang`, `pair_refine`).
- **Target model switching** — model slug is a static Set-node default; no UI
  parameter or multi-model batch run without editing the workflow.
- **Schedule / trigger** — manual trigger only; no cron or webhook for automated
  benchmark runs.
- **Error handling** — no retry logic or fallback when NVIDIA NIM or Postgres
  calls fail mid-pipeline.

#### Database

- **Schema** — `docker/postgres/init/` contains only `.gitkeep`; no
  `01-schema.sql` to create `jerga` and `results` tables.
- **Seed data** — no `02-seed-jerga.sql` with the slang corpus; `Fetch Jerga`
  will fail until rows exist.

#### Grafana

- **Dashboards** — `grafana/` contains only `.gitkeep`; no dashboard JSON for
  success-rate-by-model, success-rate-by-technique, or harm-category queries
  defined in AGENTS.md.

#### Python attacker (referenced in AGENTS.md, not present)

- **`attacker/main.py`** — CLI entry point (`--target`, `--technique`, `--limit`)
  mentioned in AGENTS.md does not exist.
- **`attacker/techniques.py`** — `VALID_TECHNIQUES` list referenced in AGENTS.md
  does not exist.
- The README lists Python as a technology, but no Python benchmark code ships
  in the repo; orchestration is intended via n8n only for now.

[Unreleased]: https://example.com/compare/HEAD
