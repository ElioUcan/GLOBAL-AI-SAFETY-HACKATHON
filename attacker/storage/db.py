"""PostgreSQL connection helpers."""

from __future__ import annotations

import os


def get_connection():
    """Open psycopg2 connection from DATABASE_URL or POSTGRES_* env vars."""
    try:
        import psycopg2
    except ImportError as exc:
        raise SystemExit(
            "psycopg2 is required. Install with: pip install -r requirements.txt"
        ) from exc

    dsn = os.getenv("DATABASE_URL")
    if dsn:
        conn = psycopg2.connect(dsn)
    else:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            user=os.getenv("POSTGRES_USER", "admin"),
            password=os.getenv("POSTGRES_PASSWORD", "changeme"),
            dbname=os.getenv("POSTGRES_DB", "slang_bench"),
        )
    conn.autocommit = False
    return conn


def fetch_jerga(conn, limit: int) -> list[dict]:
    import psycopg2.extras

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT id, term, meaning, harm_category, region, base_intent
            FROM jerga
            ORDER BY RANDOM()
            LIMIT %s;
            """,
            (limit,),
        )
        return [dict(row) for row in cur.fetchall()]
