-- Tabla auxiliar para trazabilidad de ingesta (slang_bench).
-- No la consulta el pipeline de Lizandro; solo jerga.

CREATE TABLE IF NOT EXISTS jerga_metadata (
    jerga_id           INTEGER PRIMARY KEY REFERENCES jerga(id) ON DELETE CASCADE,
    behavior_id        TEXT NOT NULL,
    semantic_category  TEXT NOT NULL,
    corpus_id_fusion   TEXT,
    confianza          SMALLINT,
    procedencia        TEXT,
    tags               JSONB NOT NULL DEFAULT '[]'::jsonb,
    fuentes            JSONB NOT NULL DEFAULT '[]'::jsonb,
    pos                TEXT,
    nivel_formalidad   TEXT,
    ingest_source      TEXT NOT NULL,
    ingest_version     TEXT NOT NULL,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_jerga_metadata_behavior ON jerga_metadata(behavior_id);
CREATE INDEX IF NOT EXISTS idx_jerga_metadata_semantic ON jerga_metadata(semantic_category);
