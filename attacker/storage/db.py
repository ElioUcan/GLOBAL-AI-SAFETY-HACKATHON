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


def _apply_seed(conn, seed: int | None) -> None:
    if seed is None:
        return
    with conn.cursor() as cur:
        # PostgreSQL setseed expects float in [-1, 1)
        cur.execute("SELECT setseed(%s)", ((seed % 1_000_000) / 1_000_000.0,))


def fetch_jerga(
    conn,
    limit: int,
    *,
    offset: int = 0,
    seed: int | None = None,
    harm_category: str | None = None,
    deterministic: bool = False,
) -> list[dict]:
    """Fetch corpus rows for benchmark runs.

    - ``deterministic=True``: stable ``ORDER BY id`` (for paired splits / control arm).
    - ``deterministic=False``: ``ORDER BY RANDOM()`` after optional ``setseed``.
    """
    import psycopg2.extras

    _apply_seed(conn, seed)
    order = "id" if deterministic else "RANDOM()"
    where = ["base_intent IS NOT NULL", "TRIM(base_intent) <> ''"]
    params: list[object] = []
    if harm_category:
        where.append("harm_category = %s")
        params.append(harm_category)
    params.extend([limit, offset])
    sql = f"""
        SELECT id, term, meaning, harm_category, region, base_intent
        FROM jerga
        WHERE {' AND '.join(where)}
        ORDER BY {order}
        LIMIT %s OFFSET %s;
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]
