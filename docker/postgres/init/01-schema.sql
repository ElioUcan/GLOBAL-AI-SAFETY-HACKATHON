-- Yucatan Slang Jailbreak Benchmark — database schema
-- Runs automatically on first Postgres boot via /docker-entrypoint-initdb.d/

-- ── Slang corpus ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS jerga (
    id            SERIAL PRIMARY KEY,
    term          TEXT NOT NULL,
    meaning       TEXT NOT NULL,
    base_intent   TEXT,
    harm_category TEXT NOT NULL,
    region        TEXT NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ── Attack results ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS results (
    id                SERIAL PRIMARY KEY,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Source term
    jerga_id          INTEGER REFERENCES jerga(id),
    base_intent       TEXT DEFAULT '',
    harm_category     TEXT DEFAULT '',
    region            TEXT DEFAULT '',

    -- Attack metadata
    attack_technique  TEXT NOT NULL,
    generated_prompt  TEXT NOT NULL,
    attacker_model_requested TEXT DEFAULT '',
    attacker_model_used      TEXT DEFAULT '',
    is_fallback_triggered    BOOLEAN NOT NULL DEFAULT FALSE,
    slang_integration_score  INTEGER DEFAULT 0,
    prompt_tokens            INTEGER DEFAULT 0,
    completion_tokens        INTEGER DEFAULT 0,
    judge_model       TEXT DEFAULT '',

    -- Target response
    target_model      TEXT NOT NULL,
    target_provider   TEXT NOT NULL DEFAULT 'nvidia_nim',
    response          TEXT,

    -- Judge verdict
    score             INTEGER NOT NULL DEFAULT 0,
    jailbreak_success BOOLEAN NOT NULL DEFAULT FALSE,
    confidence        NUMERIC(5,4) DEFAULT 0.0,
    severity          TEXT DEFAULT 'none'
                          CHECK (severity IN ('none','low','medium','high','critical')),
    harm_detected     TEXT DEFAULT 'none',
    judge_reasoning   TEXT,
    judge_output      JSONB
);

-- ── Attacker Calibration ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS attacker_calibration (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    jerga_id INTEGER REFERENCES jerga(id),
    attack_technique TEXT NOT NULL,
    term TEXT NOT NULL,
    meaning TEXT NOT NULL,
    harm_category TEXT NOT NULL,
    region TEXT NOT NULL,
    generated_prompt TEXT NOT NULL,
    attacker_model_requested TEXT NOT NULL,
    attacker_model_used TEXT NOT NULL,
    is_fallback_triggered BOOLEAN NOT NULL DEFAULT FALSE,
    slang_integration_score INTEGER NOT NULL,
    sis_reasoning TEXT,
    prompt_tokens INTEGER NOT NULL,
    completion_tokens INTEGER NOT NULL,
    calibration_phase TEXT NOT NULL
);

-- Indexes used by Grafana metric queries and ASR views
CREATE INDEX IF NOT EXISTS idx_results_target_model    ON results(target_model);
CREATE INDEX IF NOT EXISTS idx_results_technique       ON results(attack_technique);
CREATE INDEX IF NOT EXISTS idx_results_jerga_id        ON results(jerga_id);
CREATE INDEX IF NOT EXISTS idx_results_score           ON results(score);
CREATE INDEX IF NOT EXISTS idx_results_jailbreak       ON results(jailbreak_success);
CREATE INDEX IF NOT EXISTS idx_results_harm_category   ON results(harm_category);
CREATE INDEX IF NOT EXISTS idx_results_region          ON results(region);
