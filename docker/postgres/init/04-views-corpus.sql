-- Apply on live DB: psql or python migrate
-- Splits Grafana metrics by corpus_condition (slang vs neutral)

CREATE OR REPLACE VIEW v_asr_by_corpus AS
SELECT
    corpus_condition,
    COUNT(*)                                    AS total_attacks,
    SUM(jailbreak_success::int)                 AS successful_attacks,
    ROUND(AVG(jailbreak_success::int) * 100, 2) AS asr_pct,
    ROUND(AVG(score)::numeric, 2)               AS avg_score,
    ROUND(AVG(NULLIF(slang_integration_score, 0))::numeric, 2) AS avg_sis
FROM results
WHERE score BETWEEN 1 AND 5
GROUP BY corpus_condition
ORDER BY corpus_condition;

CREATE OR REPLACE VIEW v_asr_slang_vs_neutral AS
SELECT
    target_model,
    target_provider,
    SUM(CASE WHEN corpus_condition = 'slang' THEN 1 ELSE 0 END)     AS slang_n,
    ROUND(AVG(CASE WHEN corpus_condition = 'slang'
        THEN jailbreak_success::int END) * 100, 2)                   AS slang_asr_pct,
    SUM(CASE WHEN corpus_condition = 'neutral' THEN 1 ELSE 0 END)   AS neutral_n,
    ROUND(AVG(CASE WHEN corpus_condition = 'neutral'
        THEN jailbreak_success::int END) * 100, 2)                 AS neutral_asr_pct
FROM results
WHERE score BETWEEN 1 AND 5
GROUP BY target_model, target_provider
ORDER BY target_model;

CREATE OR REPLACE VIEW v_asr_by_corpus_and_harm AS
SELECT
    r.corpus_condition,
    COALESCE(NULLIF(r.harm_category, ''), j.harm_category) AS harm_category,
    COUNT(*)                                    AS total_attacks,
    ROUND(AVG(r.jailbreak_success::int) * 100, 2) AS asr_pct
FROM results r
LEFT JOIN jerga j ON r.jerga_id = j.id
WHERE r.score BETWEEN 1 AND 5
GROUP BY r.corpus_condition, COALESCE(NULLIF(r.harm_category, ''), j.harm_category)
ORDER BY harm_category, corpus_condition;
