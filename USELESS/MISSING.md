# MISSING.md — Project Completion Checklist

A detailed, actionable checklist of everything still needed to finish the
**Yucatan Slang Jailbreak Benchmark**. Grouped by area. Check items off as they
land. Items marked **[verify]** are things to investigate/confirm rather than
build from scratch.

Each task lists a **Ref:** with `path:line` location(s) so you can jump straight
to the relevant code/config. Lines are approximate and may drift as files change.

---

## 1. Database (blocking — nothing runs without this)

- [ ] **Create `docker/postgres/init/01-schema.sql`** — does not exist yet.
      Ref: `docker/postgres/init/.gitkeep:4`
  - [ ] `jerga` table: `id` (PK), `term`, `meaning`, `harm_category`, `region`
        (+ `created_at`). Must match what `Fetch Jerga` selects.
        Ref: `Yucatan Slang Jailbreak Benchmark.json:121`, `attacker/main.py:141`
  - [ ] `results` table with **exactly** the columns the storage layer writes:
        `id` (PK), `jerga_id` (FK → `jerga.id`), `attack_technique`,
        `generated_prompt`, `target_model`, `target_provider`, `response`,
        `jailbreak_success` (bool), `confidence` (numeric), `severity` (text),
        `judge_reasoning` (text), `created_at` (default now()).
        Ref: `attacker/main.py:158`, `AGENTS.md:261`, `Yucatan Slang Jailbreak Benchmark.json:643`
  - [ ] Indexes used by the Grafana metric queries (`target_model`,
        `attack_technique`, `jerga_id`).
        Ref: `AGENTS.md:338`
  - [ ] Decide `severity` storage: free text vs `CHECK`/enum
        (`none|low|medium|high`).
        Ref: `AGENTS.md:229`
- [ ] **Create `docker/postgres/init/02-seed-jerga.sql`** — does not exist yet.
      Temporary slang corpus (≥ 10–20 rows for dev).
      Ref: `docker/postgres/init/.gitkeep:5`, `AGENTS.md` (Jerga Corpus section)
  - [ ] `harm_category` values **must match** the keys in `HARM_KEYWORDS`
        (`violence`, `drugs`, `hate_speech`) or the regex pre-filter never fires.
        Ref: `attacker/main.py:96`, `Yucatan Slang Jailbreak Benchmark.json:351`
- [ ] **Apply scripts**: rebuild the Postgres volume so init hooks run
      (`docker compose down -v && docker compose up -d`).
      Ref: `compose.yml:7`, `docker/postgres/init/.gitkeep:1`
- [ ] **[verify]** Decide whether to persist `tokens_used` (captured but never
      stored — not in the `results` INSERT).
      Ref: `attacker/main.py:244`, `AGENTS.md:160`

---

## 2. Grafana dashboards

- [ ] **`grafana/` only contains `.gitkeep`** — no dashboard JSON exists.
      Build dashboards for the three AGENTS.md metric queries:
      Ref: `grafana/.gitkeep:1`, `compose.yml:92`, `AGENTS.md:338`
  - [ ] Success rate by `target_model`.  Ref: `AGENTS.md:341`
  - [ ] Success rate by `attack_technique`.
  - [ ] Most vulnerable `harm_category` (join `results` → `jerga`).
- [ ] **[verify]** Datasource provisioning connects with compose env vars and
      dashboards load against the real schema.
      Ref: `docker/grafana/provisioning/datasources/postgres.yml:1`

---

## 3. n8n workflow — `Yucatan Slang Jailbreak Benchmark.json`

- [ ] **Fix batch-loop wiring (correctness bug).** `Loop Batch (100x)` is a
      `splitInBatches` v3 node, but the loop body (`Fetch Jerga`) is connected to
      **output index 0 (done)**. In v3, output 0 = *done*, output 1 = *loop*.
      The body must hang off output 1, and `Store Result` must loop back to it.
      As wired, the 100 iterations will not execute correctly.
      Ref: `Yucatan Slang Jailbreak Benchmark.json:115` (node), `:682` (connection), `:131` (Fetch Jerga)
- [ ] **Technique rotation.** Attacker still reads a static
      `Attack Config.technique`. Derive per iteration, e.g.
      `techniques[($json.iteration - 1) % 7]` in `Generate Batch Items`.
      Ref: `Yucatan Slang Jailbreak Benchmark.json:52` (cfg-technique), `:91` (jsCode)
- [ ] **Target model switching.** `target_model` is a static default; add a
      `target_models` array and rotate per iteration (or expose as input).
      Ref: `Yucatan Slang Jailbreak Benchmark.json:58` (cfg-target-model)
- [ ] **PAIR loop (`pair_refine`).** Still a sticky note only — implement the
      multi-turn Attacker→Target→Regex→Judge sub-workflow (max 5 rounds, early
      stop at confidence ≥ 0.8).
      Ref: `Yucatan Slang Jailbreak Benchmark.json:45` (PAIR Note), `AGENTS.md:296`
- [ ] **Coverage guarantee.** `Fetch Jerga` uses `ORDER BY RANDOM() LIMIT 1`,
      which can repeat terms and does not guarantee (term × technique) coverage.
      Ref: `Yucatan Slang Jailbreak Benchmark.json:121`
- [ ] **Schedule / trigger.** Manual trigger only; add cron/webhook.
      Ref: `Yucatan Slang Jailbreak Benchmark.json:6` (manualTrigger), `:13`
- [ ] **Error handling.** No `continueOnFail`/retry on NVIDIA NIM or Postgres
      failures, so one mid-pipeline error aborts the whole batch.
      Ref: `Yucatan Slang Jailbreak Benchmark.json:643` (Store Result), `:131` (Fetch Jerga)
- [ ] **Credentials.** Postgres + NVIDIA API credentials must be bound in the
      n8n UI after import.
      Ref: `Yucatan Slang Jailbreak Benchmark.json:131` (Fetch Jerga), `:643` (Store Result)

### 3a. Embedded code & prompts inside the JSON — **[verify]** (you were right)

The workflow does embed code and prompts. Confirm each is correct and stays in
sync with `AGENTS.md` / the Python attacker:

- [ ] **JavaScript Code node** — `Generate Batch Items` (`jsCode`). Verify batch
      sizing logic and that it reads `batch_iterations` correctly.
      Ref: `Yucatan Slang Jailbreak Benchmark.json:91` (jsCode), `:100` (node)
- [ ] **Python Code node** — `Regex Pre-filter` (`language: pythonNative`).
      Ref: `Yucatan Slang Jailbreak Benchmark.json:350-351` (code), `:360` (node)
  - [ ] **Logic parity** with `quick_check`/`HARM_KEYWORDS` (keep keyword lists
        identical).  Ref: `attacker/main.py:96`, `attacker/main.py:103`
  - [ ] **Runtime support**: `pythonNative` requires the n8n Python task runner.
        Confirm the image executes it; otherwise rewrite the node in JavaScript.
        Ref: `compose.yml:48` (`N8N_RUNNERS_ENABLED`)
- [ ] **Attacker system prompt** (`systemMessage`) — matches `AGENTS.md` /
      `main.py` verbatim (confirmed). Re-check after any edit.
      Ref: `Yucatan Slang Jailbreak Benchmark.json:139`, `attacker/main.py:65`, `AGENTS.md:74`
- [ ] **Judge system prompt** (`systemMessage`) — matches `AGENTS.md` /
      `main.py` verbatim (confirmed). Re-check after any edit.
      Ref: `Yucatan Slang Jailbreak Benchmark.json:479`, `attacker/main.py:79`, `AGENTS.md:184`
- [ ] **[verify]** `lmChatNvidia` node type exists in the target n8n version and
      the model slugs are valid NVIDIA NIM models.
      Ref: `Yucatan Slang Jailbreak Benchmark.json:155` (405B), `:495` (70B), `:164`/`:504` (node type)

---

## 4. Python attacker — `attacker/`

- [ ] **[verify] Judge output schema is under-specified (correctness risk).**
      Both system prompts were checked — Attacker is correct/consistent; Judge is
      consistent **but** only says *"Respond ONLY with a valid JSON object"*
      without enumerating the required keys (`jailbreak_success`, `confidence`
      0–1, `harm_detected`, `reasoning`, `severity` ∈ `none|low|medium|high`).
      The n8n workflow enforces this with a Structured Output Parser, but
      `judge_agent()` does **not** — it leans on the `_parse_judge_json` fallback.
      Ref: `attacker/main.py:79` (prompt), `attacker/main.py:257` (judge_agent), `attacker/main.py:286` (parser), `AGENTS.md:217` (schema)
  - [ ] **Action:** add the explicit output schema to the Judge system prompt
        (or the user template).
- [ ] **Retry/backoff** for NVIDIA NIM rate limits / transient errors (a single
      failure per term is logged and skipped, no retry).
      Ref: `attacker/main.py:200` (`_completion`), `attacker/main.py:491` (except)
- [ ] **[verify]** `from techniques import ...` works as
      `python attacker/main.py` (script dir on `sys.path`) but breaks if imported
      as a package. Add `attacker/__init__.py` only if importing as a module.
      Ref: `attacker/main.py:34`
- [ ] **Committed test suite.** The temporary mock-based harness was removed —
      add a permanent `tests/` (fake DB + mocked `_completion`).
      Ref: `attacker/main.py:200` (mock target), `attacker/main.py:111` (DB target)
- [ ] **[verify]** Confirm dependency versions install cleanly.
      Ref: `attacker/requirements.txt:2`

---

## 5. Attack techniques — **[verify] needs more research**

- [ ] **Deepen technique definitions.** `TECHNIQUE_DESCRIPTIONS` (and the
      AGENTS.md table) are one-line summaries. Research/document each more
      rigorously: concrete slang example, citations/prior work, expected failure
      modes, and what "success" looks like per technique.
      Ref: `attacker/techniques.py:22`, `AGENTS.md:101`, `Yucatan Slang Jailbreak Benchmark.json:87`
- [ ] **Calibrate `pair_refine` in rotation.** It runs up to 5 LLM round-trips —
      decide if it belongs in the round-robin or as a separate explicit mode.
      Ref: `attacker/techniques.py:39` (MULTI_TURN), `attacker/techniques.py:52` (rotation), `attacker/main.py:374` (run_pair_attack)
- [ ] **Expand `HARM_KEYWORDS`.** Only 3 categories with a few Spanish keywords;
      research a fuller, validated set and keep n8n + Python copies identical.
      Ref: `attacker/main.py:96`, `Yucatan Slang Jailbreak Benchmark.json:351`

---

## 6. Documentation & repo hygiene

- [ ] **README** — add a "Python attacker" usage section (install, env vars,
      `--target/--technique/--limit/--dry-run`). Python is listed as a technology
      with no run instructions.
      Ref: `README.md:9` (badge), `README.md:31` (Running section)
- [ ] **[verify]** `.env` flow — document that the Python CLI uses `POSTGRES_*`
      with host `localhost` (vs `postgres` inside compose) and needs
      `NVIDIA_API_KEY`.
      Ref: `attacker/main.py:111` (get_connection), `.env.example:24`
- [ ] **LICENSE** — none present; add one if publishing.  Ref: (repo root)
- [ ] **`.gitignore`** — confirm `__pycache__/` and other artifacts are ignored
      (currently only `.env`).
      Ref: `.gitignore:1`
- [ ] **`webscrapper.py`** — placeholder only; implement the planned scraper that
      upserts into `jerga` (or remove it if unused).
      Ref: `webscrapper.py:1`

---

## 7. End-to-end validation (do last)

- [ ] Boot the full stack (`docker compose up -d --build`) and confirm Postgres
      init scripts ran (tables + seed rows exist).  Ref: `compose.yml:7`
- [ ] Run the Python attacker against a small `--limit` with a **real**
      `NVIDIA_API_KEY` and confirm rows land in `results`.
      Ref: `attacker/main.py:451` (main)
- [ ] Import and run the n8n workflow once; confirm a row is written and the
      batch loop iterates the configured count.
      Ref: `Yucatan Slang Jailbreak Benchmark.json:13`
- [ ] Open Grafana and confirm all three dashboards render real data.
      Ref: `compose.yml:71`

---

### Notes on API keys (answer to a recurring question)

- **Mocked/unit tests & `--dry-run`:** no API key, no network, no DB needed.
  Ref: `attacker/main.py:444` (`--dry-run` flag)
- **Any real run (Python CLI or n8n):** a valid **`NVIDIA_API_KEY`** is required
  (attacker, target, and judge all call NVIDIA NIM), plus a live PostgreSQL with
  the `jerga` and `results` tables populated.
  Ref: `attacker/main.py:468` (key check), `.env.example:25`
