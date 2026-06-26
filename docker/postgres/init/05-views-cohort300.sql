-- Primary paper cohort: first 300 scored rows per arm (ORDER BY id).
-- Matches draft_submission.md §Recorte de muestra (N=300 slang + N=300 neutral).

CREATE OR REPLACE VIEW v_results_cohort300 AS
SELECT * FROM (
    SELECT * FROM results
    WHERE score BETWEEN 1 AND 5 AND corpus_condition = 'slang'
    ORDER BY id
    LIMIT 300
) AS slang_rows
UNION ALL
SELECT * FROM (
    SELECT * FROM results
    WHERE score BETWEEN 1 AND 5 AND corpus_condition = 'neutral'
    ORDER BY id
    LIMIT 300
) AS neutral_rows;

CREATE OR REPLACE VIEW v_asr_by_corpus_cohort300 AS
SELECT
    corpus_condition,
    COUNT(*)                                    AS total_attacks,
    SUM(jailbreak_success::int)                 AS successful_attacks,
    ROUND(AVG(jailbreak_success::int) * 100, 2) AS asr_pct,
    ROUND(AVG(score)::numeric, 2)               AS avg_score,
    ROUND(AVG(NULLIF(slang_integration_score, 0))::numeric, 2) AS avg_sis
FROM v_results_cohort300
GROUP BY corpus_condition
ORDER BY corpus_condition;

CREATE OR REPLACE VIEW v_asr_slang_vs_neutral_cohort300 AS
SELECT
    target_model,
    target_provider,
    SUM(CASE WHEN corpus_condition = 'slang' THEN 1 ELSE 0 END)     AS slang_n,
    ROUND(AVG(CASE WHEN corpus_condition = 'slang'
        THEN jailbreak_success::int END) * 100, 2)                   AS slang_asr_pct,
    SUM(CASE WHEN corpus_condition = 'neutral' THEN 1 ELSE 0 END)   AS neutral_n,
    ROUND(AVG(CASE WHEN corpus_condition = 'neutral'
        THEN jailbreak_success::int END) * 100, 2)                 AS neutral_asr_pct
FROM v_results_cohort300
GROUP BY target_model, target_provider
HAVING SUM(CASE WHEN corpus_condition = 'slang' THEN 1 ELSE 0 END) > 0
    OR SUM(CASE WHEN corpus_condition = 'neutral' THEN 1 ELSE 0 END) > 0
ORDER BY target_model;

CREATE OR REPLACE VIEW v_asr_by_corpus_and_harm_cohort300 AS
SELECT
    r.corpus_condition,
    COALESCE(NULLIF(r.harm_category, ''), j.harm_category) AS harm_category,
    COUNT(*)                                    AS total_attacks,
    ROUND(AVG(r.jailbreak_success::int) * 100, 2) AS asr_pct
FROM v_results_cohort300 r
LEFT JOIN jerga j ON r.jerga_id = j.id
GROUP BY r.corpus_condition, COALESCE(NULLIF(r.harm_category, ''), j.harm_category)
ORDER BY harm_category, corpus_condition;

CREATE OR REPLACE VIEW v_asr_by_technique_cohort300 AS
SELECT
    attack_technique,
    COUNT(*)                                    AS total_attacks,
    SUM(jailbreak_success::int)                 AS successful_attacks,
    ROUND(AVG(jailbreak_success::int) * 100, 2) AS asr_pct
FROM v_results_cohort300
WHERE corpus_condition = 'slang'
GROUP BY attack_technique
ORDER BY asr_pct DESC;

CREATE OR REPLACE VIEW v_asr_by_model_cohort300 AS
SELECT
    corpus_condition,
    target_model,
    target_provider,
    COUNT(*)                                    AS total_attacks,
    ROUND(AVG(jailbreak_success::int) * 100, 2) AS asr_pct
FROM v_results_cohort300
GROUP BY corpus_condition, target_model, target_provider
ORDER BY corpus_condition, asr_pct DESC;

-- Single-row thesis metrics for Grafana stat panels (paper figure export).
CREATE OR REPLACE VIEW v_thesis_findings_cohort300 AS
SELECT
    MAX(CASE WHEN corpus_condition = 'slang' THEN total_attacks END)::int     AS slang_n,
    MAX(CASE WHEN corpus_condition = 'slang' THEN successful_attacks END)::int AS slang_jailbreaks,
    MAX(CASE WHEN corpus_condition = 'slang' THEN asr_pct END)                  AS slang_asr_pct,
    MAX(CASE WHEN corpus_condition = 'neutral' THEN total_attacks END)::int     AS neutral_n,
    MAX(CASE WHEN corpus_condition = 'neutral' THEN successful_attacks END)::int AS neutral_jailbreaks,
    MAX(CASE WHEN corpus_condition = 'neutral' THEN asr_pct END)                AS neutral_asr_pct,
    ROUND(
        MAX(CASE WHEN corpus_condition = 'slang' THEN asr_pct END)
        - MAX(CASE WHEN corpus_condition = 'neutral' THEN asr_pct END),
        2
    ) AS delta_asr_pp,
    ROUND(
        MAX(CASE WHEN corpus_condition = 'slang' THEN asr_pct END)
        / NULLIF(MAX(CASE WHEN corpus_condition = 'neutral' THEN asr_pct END), 0),
        2
    ) AS relative_risk_x
FROM v_asr_by_corpus_cohort300;
