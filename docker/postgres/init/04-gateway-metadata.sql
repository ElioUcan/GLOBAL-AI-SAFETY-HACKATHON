-- Idempotent migration: gateway metadata columns for results table
-- Safe to re-run; preserves existing data and Grafana views.

ALTER TABLE results ADD COLUMN IF NOT EXISTS target_model_requested TEXT DEFAULT '';
ALTER TABLE results ADD COLUMN IF NOT EXISTS target_model_used TEXT DEFAULT '';
ALTER TABLE results ADD COLUMN IF NOT EXISTS judge_model_requested TEXT DEFAULT '';
ALTER TABLE results ADD COLUMN IF NOT EXISTS judge_model_used TEXT DEFAULT '';
ALTER TABLE results ADD COLUMN IF NOT EXISTS judge_provider TEXT DEFAULT '';
ALTER TABLE results ADD COLUMN IF NOT EXISTS evaluation_method TEXT DEFAULT 'llm_judge';
ALTER TABLE results ADD COLUMN IF NOT EXISTS raw_judge_output TEXT;
ALTER TABLE results ADD COLUMN IF NOT EXISTS judge_parse_error TEXT;
ALTER TABLE results ADD COLUMN IF NOT EXISTS request_latency_ms INTEGER DEFAULT 0;
ALTER TABLE results ADD COLUMN IF NOT EXISTS estimated_cost NUMERIC(12,6);
ALTER TABLE results ADD COLUMN IF NOT EXISTS provider_request_id TEXT;
ALTER TABLE results ADD COLUMN IF NOT EXISTS run_id TEXT;

-- Backfill target_model_used from legacy target_model where empty
UPDATE results
SET target_model_used = target_model
WHERE (target_model_used IS NULL OR target_model_used = '')
  AND target_model IS NOT NULL AND target_model <> '';

UPDATE results
SET target_model_requested = target_model
WHERE (target_model_requested IS NULL OR target_model_requested = '')
  AND target_model IS NOT NULL AND target_model <> '';

UPDATE results
SET judge_model_used = judge_model
WHERE (judge_model_used IS NULL OR judge_model_used = '')
  AND judge_model IS NOT NULL AND judge_model <> '';

CREATE INDEX IF NOT EXISTS idx_results_evaluation_method ON results(evaluation_method);
CREATE INDEX IF NOT EXISTS idx_results_run_id ON results(run_id);
