"""Lightweight schema patches (safe to run on live DB)."""

from __future__ import annotations


def ensure_results_extensions(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            ALTER TABLE results
                ADD COLUMN IF NOT EXISTS corpus_condition TEXT NOT NULL DEFAULT 'slang';
            """
        )
        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_results_corpus_condition
                ON results(corpus_condition);
            """
        )
    conn.commit()
