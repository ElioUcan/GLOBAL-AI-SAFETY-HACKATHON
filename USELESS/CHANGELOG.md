# Changelog

All notable changes to the Yucatan Slang Jailbreak Benchmark are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## V0.1.4

### Plain-language summary
- We updated the n8n visual workflow so it follows the same logic as `main.py`.
  In simple terms: n8n now knows how to run each slang test, score the answer
  from 1 to 5, save the full result, and repeat the process in a batch.

### Changed
- **n8n workflow aligned with `main.py`** — updated
  `Yucatan Slang Jailbreak Benchmark.json` so the visual workflow follows the
  current benchmark contract: `Fetch Jerga → Attacker → Target → Regex
  pre-filter → Judge 1-5 → Storage`.
- **Batch loop fixed** — `Loop Batch (100x)` now sends `Fetch Jerga` through the
  loop output, while the done output remains empty. `Store Result` still returns
  to `Loop Batch (100x)` to continue the next item.
- **Regex verdict updated** — regex hits now emit a complete Judge-compatible
  payload with `score: 5`, `jailbreak_success`, `confidence`, `harm_detected`,
  `reasoning`, and `severity`.
- **Judge output updated** — the Judge prompt and structured parser now require
  the 1-5 scoring contract, including `score`, `jailbreak_success`,
  `confidence`, `harm_detected`, `reasoning`, and `severity`.
- **Storage mapping updated** — `Store Result` now maps `score`,
  `harm_detected`, and `judge_output` in addition to the existing result fields.
- **Postgres credential guidance added** — workflow notes now specify the
  expected n8n credential name and Docker-network connection values for
  `Fetch Jerga` and `Store Result`.

### Validation
- The workflow JSON was validated with `python -m json.tool`.

### Notes
- n8n credentials are local to each n8n instance. They are not stored in the
  repo and are not exported inside `Yucatan Slang Jailbreak Benchmark.json`.
  After pulling these changes and importing the workflow, each teammate must
  create their own Postgres credential (`slang_bench_postgres`) and configure
  NVIDIA credentials/API keys in their local n8n UI.

### Pending
- **Re-import the updated workflow JSON in n8n** so the UI uses the latest repo
  version, not an older local copy.
- **Configure required credentials** in the n8n UI: Postgres credentials for
  `Fetch Jerga` and `Store Result`, plus NVIDIA credentials/API key for the LLM
  nodes and Target HTTP request.
- **Run `main.py` end-to-end first** with a real `NVIDIA_API_KEY`, using a small
  controlled run (`--limit 1`, then 5-10) and confirm rows land in `results`.
- **Run n8n end-to-end next** with a small batch (`batch_iterations = 1`, then
  3-5) and confirm it writes the same kind of rows to `results`.
- **Confirm Grafana renders real benchmark data** from `results`: model,
  technique, harm category, score, severity, and jailbreak-success metrics.
- **Start collecting evidence for the research hypothesis**: regional Mexican
  slang may help bypass safety filters because the model does not understand the
  cultural context well enough. The results do not need to prove that upfront;
  the benchmark should also reveal if the weakness comes from neutral Spanish,
  slang, prompt structure, model-specific behavior, or another repeatable gap.

## V0.1.3

### Changed
- **Hybrid result storage types** — `results.response` and
  `results.judge_reasoning` are now `TEXT`, while `results.judge_output` remains
  `JSONB` for the complete structured Judge payload. This avoids invalid JSONB
  inserts when the target model or Judge reasoning returns plain text.
- **Python storage parity** — `attacker/storage/results.py` now stores
  `harm_detected` and the full `judge_output` object, using psycopg2's JSON
  adapter for the JSONB field.

### Reason
- The problem came from a mismatch between the database schema and what the
  benchmark actually produces. `main.py` receives the Target model response as
  plain text, and the Judge `reasoning` is also plain text. Those values were
  being inserted into `response` and `judge_reasoning`, but both columns were
  defined as `JSONB`.
- This matters because PostgreSQL only accepts valid JSON in `JSONB` columns.
  A normal model response like `Lo siento, no puedo ayudar con eso.` is useful
  benchmark data, but it is not a valid JSON document by itself. That could make
  the run fail at the final Storage step, after Attacker, Target, Regex, and
  Judge had already completed.
- The effect on the flow was that a successful evaluation could still fail to
  become a result: no row in `results`, no Grafana metric, and no evidence to
  compare models. The fix keeps free-form text in `TEXT` columns and keeps the
  structured Judge verdict in `judge_output JSONB`, where JSONB is useful for
  auditing and querying the complete score payload.

### Validated
- **`main.py` is the current source of truth for the flow** — it represents
  `Fetch Jerga → Attacker → Target → Regex pre-filter → Judge 1-5 → Storage`.
- **PostgreSQL is ready for the flow** — Docker created `attacker_calibration`,
  `jerga`, and `results`; the seed loaded 10 slang rows across `drugs`,
  `hate_speech`, and `violence`.
- **The Python path loads correctly** — `python -m attacker.main --help` and
  `python -m attacker.main models` run successfully, and `run` stops before
  execution when `NVIDIA_API_KEY` is missing.
- **Grafana is pointed at the right data model** — dashboard queries read from
  `results` and `jerga`, which are the tables populated by the benchmark flow.

### Pending
- **Run controlled tests in `main.py`** — first validate Python-to-Postgres
  reads, then run one real benchmark with `NVIDIA_API_KEY`, and confirm a valid
  row lands in `results`.
- **Confirm Grafana with real output** — after `main.py` writes at least one
  row, verify that dashboard panels render actual metrics.
- **Validate n8n in the UI** — re-import the updated workflow JSON, configure
  credentials, run a 1-3 item batch, and confirm rows land in `results`.
- **Use n8n only after Python passes** — once `main.py` produces valid results,
  mirror the same flow in n8n and run the visual workflow to start generating
  benchmark data.
- **Defer model selection** — choose Attacker, Judge, and Target model counts
  after the end-to-end flow works in `main.py` and is mirrored in n8n.

### Notes
- Existing Postgres volumes will not pick up `01-schema.sql` changes
  automatically. For a clean dev reset, run `docker compose down -v` and then
  `docker compose up -d --build`.

## V0.1.2

### Added
- **Python attacker package** implementing the AGENTS.md pipeline as a CLI
  alternative to the n8n workflow (`Fetch Jerga → Attacker → Target → Regex
  pre-filter → Judge → Storage`):
  - `attacker/main.py` — entry point with `--target`, `--technique`, `--limit`,
    and `--dry-run` flags. Routes all LLM calls (attacker, target, judge) through
    LiteLLM to NVIDIA NIM using the exact models, temperatures, and prompts from
    AGENTS.md (Llama 405B @ 0.9 attacker, target @ 0.7/512, Llama 70B @ 0.0 judge).
    Includes the regex pre-filter (`quick_check` + `HARM_KEYWORDS`), the PAIR
    multi-turn loop (`run_pair_attack`, max 5 rounds, early stop at confidence
    ≥ 0.8), defensive judge-JSON parsing, and `store_result` writing the AGENTS.md
    `results` columns.
  - `attacker/techniques.py` — `VALID_TECHNIQUES` (all seven techniques),
    `TECHNIQUE_DESCRIPTIONS`, `MULTI_TURN_TECHNIQUES`, and helpers `is_valid`,
    `is_multi_turn`, `technique_for_iteration` (round-robin rotation).
  - `attacker/requirements.txt` — `litellm`, `psycopg2-binary`, `python-dotenv`.
- **Technique rotation (Python)** — omitting `--technique` cycles through all
  seven techniques across the batch via `technique_for_iteration`.
- **Target model switching (Python)** — `--target` selects any NVIDIA NIM slug;
  `split_model_slug` records `target_model` / `target_provider` separately.

### Resolved
- **Python attacker gap** (from V0.1.1) — `attacker/main.py` and
  `attacker/techniques.py` now exist and implement the AGENTS.md pipeline. The
  technique-rotation and target-model-switching gaps are addressed for the
  Python path; the equivalent n8n-workflow gaps remain open (see V0.1.1).

### Notes
- The CLI requires the `jerga` and `results` tables (still gapped — no
  `01-schema.sql` / `02-seed-jerga.sql`) and a `NVIDIA_API_KEY`. `--dry-run`
  works without either and previews the per-iteration technique plan.

### Next improvements (`Yucatan Slang Jailbreak Benchmark.json`)

The Python attacker now covers the full AGENTS.md task, but the n8n workflow
still lags behind. To bring the workflow to parity:

- **Fix the batch-loop wiring** — `Loop Batch (100x)` is a `splitInBatches`
  (v3 "Loop Over Items") node, but its loop body (`Fetch Jerga`) is connected to
  **output index 0 (done)**. In v3, output 0 is *done* and output 1 is *loop*;
  the body must hang off output 1, with `Store Result` looping back to the node.
  As wired, the 100 iterations will not execute correctly.
- **Technique rotation** — the Attacker still reads a static
  `Attack Config.technique`. Derive the technique per iteration (e.g.
  `techniques[($json.iteration - 1) % 7]` in `Generate Batch Items`) so a single
  run exercises all seven techniques.
- **Target model switching** — `target_model` is still a static default; add a
  `target_models` array and rotate per iteration (or expose it as a workflow
  input) so one run benchmarks multiple NVIDIA NIM models.
- **PAIR loop (`pair_refine`)** — still sticky-note only; implement the
  multi-turn Attacker→Target→Regex→Judge sub-workflow (max 5 rounds, early stop
  at confidence ≥ 0.8) and route `pair_refine` iterations into it.
- **Coverage guarantee** — `Fetch Jerga` uses `ORDER BY RANDOM() LIMIT 1`, which
  can repeat terms and does not guarantee (term × technique) coverage; consider
  iterating the corpus deterministically.
- **`tokens_used` persistence** — `Extract Target Response` captures
  `tokens_used`, but the `Store Result` INSERT drops it; add the column or map it.
- **Schedule / trigger** — manual trigger only; add a cron/schedule or webhook
  trigger for automated runs.
- **Error handling** — no `continueOnFail` or retry on NVIDIA NIM / Postgres
  failures, so a single mid-pipeline error aborts the whole batch.

## V0.1.1

### Added
- **Jerga corpus data source** section in `AGENTS.md` — documents temporary bootstrap via
  `docker/postgres/init/02-seed-jerga.sql` and planned web scraper for ongoing ingestion.
- **100-iteration batch loop** in `Yucatan Slang Jailbreak Benchmark.json`:
  `Attack Config.batch_iterations` (default 100) → `Generate Batch Items` →
  `Loop Batch (100x)` (Split In Batches) → pipeline → `Store Result` loops back until done.

### Changed
- `AGENTS.md` benchmark coverage raised from 3–5 prompts to **100 iterations** per execution.
- CLI example in `AGENTS.md` updated to `--limit 100`.

### Known gaps

#### n8n workflow (not yet implemented)

- **Credentials** — Postgres and NVIDIA API credentials must be configured
  manually in n8n after import (`Fetch Jerga`, `Store Result`, Attacker LLM,
  Judge LLM). Target LLM reads `$env.NVIDIA_API_KEY` from the container env.
- **PAIR loop (`pair_refine`)** — multi-turn attacker→target→judge iteration
  (max 5 rounds, early stop at confidence ≥ 0.8) is documented via sticky note
  only; needs a sub-workflow or Loop node.
- **Technique rotation** — Attack Config still defaults to a single technique
  (`translation_transfer`). No automatic cycling across the other six techniques
  (`semantic_obfuscation`, `crescendo`, `codeswitching`, `roleplay_wrap`,
  `manyshot_slang`, `pair_refine`).
  - **Next actions:**
    1. Add a `techniques` array (or separate Code node) listing all seven valid techniques.
    2. Derive the active technique per iteration, e.g.
       `techniques[($json.iteration - 1) % 7]` inside `Generate Batch Items` or a new Set node.
    3. Pass the derived `technique` through the pipeline instead of the static Attack Config value.
    4. Verify Grafana “success rate by technique” query returns all seven buckets after a full run.
- **Target model switching** — model slug is still a static Set-node default
  (`meta/llama-3.1-8b-instruct`); no UI parameter or multi-model batch run.
  - **Next actions:**
    1. Add a `target_models` array in Attack Config with all four NVIDIA NIM slugs from AGENTS.md.
    2. Derive the active model per iteration, e.g.
       `target_models[Math.floor(($json.iteration - 1) / 7) % 4]` when paired with technique rotation.
    3. Wire the derived slug into `Extract Adversarial Prompt` → Target LLM HTTP body.
    4. Optionally expose `target_model` as a workflow input parameter for single-model runs.
    5. Confirm each model slug is written to `results.target_model` for per-model Grafana panels.
- **Schedule / trigger** — manual trigger only; no cron or webhook for automated
  benchmark runs.
- **Error handling** — no retry logic or fallback when NVIDIA NIM or Postgres
  calls fail mid-pipeline.

#### Database

- **Schema** — `docker/postgres/init/` contains only `.gitkeep`; no
  `01-schema.sql` to create `jerga` and `results` tables.
- **Seed data** — no `02-seed-jerga.sql` with the slang corpus yet; `Fetch Jerga`
  will fail until rows exist. AGENTS.md documents this file as the temporary bootstrap;
  a web scraper will replace it as the primary ingestion path later.
  - **Next actions:**
    1. Create `01-schema.sql` with `jerga` and `results` table definitions.
    2. Create `02-seed-jerga.sql` with an initial slang corpus (≥ 10 rows for dev).
    3. Rebuild Postgres volume (`docker compose down -v && docker compose up -d`) to apply init scripts.
    4. Later: build scraper service that upserts into `jerga` and retire static seed updates.

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

## V0.1.0

### Added
- `Yucatan Slang Jailbreak Benchmark.json` — full n8n workflow implementing the AGENTS.md pipeline:
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
- **Batch coverage** — single attack per execution (superseded in [Unreleased] by
  100-iteration loop).
- **Technique rotation** — Attack Config defaults to `translation_transfer`; no
  loop over the other six techniques (see [Unreleased] for next actions).
- **Target model switching** — model slug is a static Set-node default (see
  [Unreleased] for next actions).
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
