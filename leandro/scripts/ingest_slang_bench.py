#!/usr/bin/env python3
"""
ingest_slang_bench.py

Puebla slang_bench.jerga (+ jerga_metadata) desde corpus con glosa y HarmBench ES.
Idempotente: recrea jerga_metadata y repuebla jerga (no toca results).

Uso (desde la raíz del repo hackathon):
  python3 leandro/scripts/ingest_slang_bench.py --dry-run
  python3 leandro/scripts/ingest_slang_bench.py --apply

Variables de entorno (defaults para compose Lizandro en puerto 5433):
  POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

LEANDRO_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = LEANDRO_ROOT.parent
DEFAULT_CORPUS = LEANDRO_ROOT / "datasets/originales/dataset_combinado.json"
DEFAULT_HARMBENCH = LEANDRO_ROOT / "harmbench/harmbench_behaviors_text_no_copyright_es.csv"
METADATA_SQL = Path(__file__).resolve().parent / "sql/slang_bench_jerga_metadata.sql"
INGEST_VERSION = "1.1.0"

LIZANDRO_CATEGORIES = ("violence", "drugs", "hate_speech")

# HarmBench SemanticCategory → categorías Lizandro (regex HARM_KEYWORDS + seed)
SEMANTIC_TO_LIZANDRO: dict[str, str] = {
    "chemical_biological": "drugs",
    "misinformation_disinformation": "hate_speech",
    "harassment_bullying": "hate_speech",
    "harmful": "violence",
    "cybercrime_intrusion": "violence",
    "illegal": "violence",
}

DRUG_HINTS = re.compile(
    r"\b(droga|fentanil|mdma|opioid|safrol|metanfet|cocaína|cocaina|heroína|heroina|"
    r"narcót|narcot|químico|quimico|precursor|sintetiz|laboratorio|pastilla)\b",
    re.I,
)
VIOLENCE_HINTS = re.compile(
    r"\b(matar|sicario|bomba|golpear|arma|dispar|apuñal|apunal|violencia|asesin)\b",
    re.I,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_corpus(path: Path, min_confianza: int) -> list[dict]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    entradas = raw if isinstance(raw, list) else raw.get("entradas", [])
    out = []
    for e in entradas:
        conf = e.get("confianza")
        if conf is None or conf < min_confianza:
            continue
        significado = (e.get("significado") or "").strip()
        termino = (e.get("termino") or "").strip()
        if not termino or not significado:
            continue
        out.append(e)
    out.sort(key=lambda x: (x.get("termino", "").lower(), x.get("id_fusion", "")))
    return out


def load_harmbench(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    rows.sort(key=lambda r: r["BehaviorID"])
    return rows


def map_harm_category(semantic: str, behavior_text: str) -> str:
    if semantic == "illegal":
        if DRUG_HINTS.search(behavior_text):
            return "drugs"
        if VIOLENCE_HINTS.search(behavior_text):
            return "violence"
        return "violence"
    return SEMANTIC_TO_LIZANDRO.get(semantic, "violence")


def bucket_behaviors_by_harm(behaviors: list[dict]) -> dict[str, list[dict]]:
    """Agrupa behaviors HarmBench en pools por harm_category Lizandro (ordenados por BehaviorID)."""
    pools: dict[str, list[dict]] = {c: [] for c in LIZANDRO_CATEGORIES}
    for beh in behaviors:
        cat = map_harm_category(beh["SemanticCategory"], beh["Behavior"])
        pools[cat].append(beh)
    for cat in LIZANDRO_CATEGORIES:
        pools[cat].sort(key=lambda r: r["BehaviorID"])
        if not pools[cat]:
            raise SystemExit(f"Sin behaviors HarmBench mapeables a harm_category={cat!r}.")
    return pools


def assign_behaviors(terms: list[dict], behaviors: list[dict], per_term: int) -> list[dict]:
    """Empareja cada término con `per_term` behaviors, round-robin balanceado por harm_category.

    Con per_term=3: cada término recibe exactamente un behavior de violence, drugs y hate_speech.
    Con otros valores: rota categorías violence → drugs → hate_speech por asignación.
    """
    pools = bucket_behaviors_by_harm(behaviors)
    counters = {c: 0 for c in LIZANDRO_CATEGORIES}
    pairs: list[dict] = []

    for term_idx, term in enumerate(terms):
        if per_term == 3:
            cats = LIZANDRO_CATEGORIES
        else:
            cats = [LIZANDRO_CATEGORIES[(term_idx + j) % 3] for j in range(per_term)]

        for cat in cats:
            pool = pools[cat]
            beh = pool[counters[cat] % len(pool)]
            counters[cat] += 1
            pairs.append({"term": term, "behavior": beh})

    return pairs


def build_rows(
    pairs: list[dict],
    *,
    region: str,
    corpus_path: Path,
) -> list[dict]:
    rows = []
    for pair in pairs:
        t = pair["term"]
        b = pair["behavior"]
        behavior_text = b["Behavior"]
        semantic = b["SemanticCategory"]
        rows.append(
            {
                "term": t["termino"],
                "meaning": t["significado"],
                "base_intent": behavior_text,
                "harm_category": map_harm_category(semantic, behavior_text),
                "region": region,
                "metadata": {
                    "behavior_id": b["BehaviorID"],
                    "semantic_category": semantic,
                    "corpus_id_fusion": t.get("id_fusion"),
                    "confianza": t.get("confianza"),
                    "procedencia": t.get("procedencia"),
                    "tags": t.get("tags") or [],
                    "fuentes": t.get("fuentes") or [],
                    "pos": t.get("pos"),
                    "nivel_formalidad": t.get("nivel_formalidad"),
                    "ingest_source": str(corpus_path.relative_to(LEANDRO_ROOT)),
                    "ingest_version": INGEST_VERSION,
                },
            }
        )
    return rows


def get_connection():
    try:
        import psycopg2
    except ImportError as exc:
        raise SystemExit("Instala psycopg2: pip install psycopg2-binary") from exc

    dsn = os.getenv("DATABASE_URL")
    if dsn:
        return psycopg2.connect(dsn)
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5433"),
        user=os.getenv("POSTGRES_USER", "admin"),
        password=os.getenv("POSTGRES_PASSWORD", "changeme"),
        dbname=os.getenv("POSTGRES_DB", "slang_bench"),
    )


def ensure_metadata_table(conn) -> None:
    sql = METADATA_SQL.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def apply_ingest(conn, rows: list[dict]) -> None:
    with conn.cursor() as cur:
        cur.execute("TRUNCATE jerga_metadata")
        cur.execute("TRUNCATE jerga RESTART IDENTITY CASCADE")

        for row in rows:
            cur.execute(
                """
                INSERT INTO jerga (term, meaning, base_intent, harm_category, region)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    row["term"],
                    row["meaning"],
                    row["base_intent"],
                    row["harm_category"],
                    row["region"],
                ),
            )
            jerga_id = cur.fetchone()[0]
            m = row["metadata"]
            cur.execute(
                """
                INSERT INTO jerga_metadata (
                    jerga_id, behavior_id, semantic_category,
                    corpus_id_fusion, confianza, procedencia,
                    tags, fuentes, pos, nivel_formalidad,
                    ingest_source, ingest_version
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    jerga_id,
                    m["behavior_id"],
                    m["semantic_category"],
                    m["corpus_id_fusion"],
                    m["confianza"],
                    m["procedencia"],
                    json.dumps(m["tags"], ensure_ascii=False),
                    json.dumps(m["fuentes"], ensure_ascii=False),
                    m["pos"],
                    m["nivel_formalidad"],
                    m["ingest_source"],
                    m["ingest_version"],
                ),
            )
    conn.commit()


def print_summary(rows: list[dict]) -> None:
    from collections import Counter

    harm = Counter(r["harm_category"] for r in rows)
    region = Counter(r["region"] for r in rows)
    semantic = Counter(r["metadata"]["semantic_category"] for r in rows)
    unique_terms = len({r["term"] for r in rows})

    print(f"\n=== Resumen ingesta ({_now_iso()}) ===")
    print(f"  Filas jerga:        {len(rows)}")
    print(f"  Términos únicos:    {unique_terms}")
    print(f"  harm_category:      {dict(harm)}")
    print(f"  region:             {dict(region)}")
    print(f"  semantic (metadata): {dict(semantic)}")
    print("\n  Ejemplos:")
    for row in rows[:3]:
        print(
            f"    • {row['term']!r} | harm={row['harm_category']} | "
            f"behavior={row['metadata']['behavior_id']}"
        )


def verify_db(conn) -> None:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM jerga")
        n_jerga = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM jerga_metadata")
        n_meta = cur.fetchone()[0]
        cur.execute(
            """
            SELECT harm_category, COUNT(*) FROM jerga
            GROUP BY harm_category ORDER BY harm_category
            """
        )
        harm = cur.fetchall()
        cur.execute(
            """
            SELECT region, COUNT(*) FROM jerga
            GROUP BY region ORDER BY region
            """
        )
        reg = cur.fetchall()
        cur.execute(
            """
            SELECT j.term, j.meaning, j.harm_category, j.base_intent, m.behavior_id, m.semantic_category
            FROM jerga j
            JOIN jerga_metadata m ON m.jerga_id = j.id
            ORDER BY j.id
            LIMIT 5
            """
        )
        samples = cur.fetchall()

    print("\n=== Verificación DB ===")
    print(f"  jerga: {n_jerga} | jerga_metadata: {n_meta}")
    print("  Por harm_category:", dict(harm))
    print("  Por region:", dict(reg))
    print("  Muestra (5 filas):")
    for s in samples:
        term, meaning, harm, intent, bid, sem = s
        print(f"    id term={term!r} harm={harm} sem={sem} behavior={bid}")
        print(f"       meaning={meaning[:60]}...")
        print(f"       base_intent={intent[:60]}...")


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingesta corpus → slang_bench.jerga")
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--harmbench", type=Path, default=DEFAULT_HARMBENCH)
    parser.add_argument("--min-confianza", type=int, default=2)
    parser.add_argument("--behaviors-per-term", type=int, default=3)
    parser.add_argument("--region", default="Mexico")
    parser.add_argument("--dry-run", action="store_true", help="Solo planifica, no escribe DB")
    parser.add_argument("--apply", action="store_true", help="Escribe en Postgres")
    parser.add_argument("--verify-only", action="store_true", help="Solo consultas de verificación")
    args = parser.parse_args()

    if args.verify_only:
        conn = get_connection()
        try:
            verify_db(conn)
        finally:
            conn.close()
        return 0

    if not args.dry_run and not args.apply:
        parser.error("Indica --dry-run o --apply")

    if not args.corpus.is_file():
        print(f"Corpus no encontrado: {args.corpus}", file=sys.stderr)
        return 1
    if not args.harmbench.is_file():
        print(f"HarmBench no encontrado: {args.harmbench}", file=sys.stderr)
        return 1

    terms = load_corpus(args.corpus, args.min_confianza)
    behaviors = load_harmbench(args.harmbench)
    pairs = assign_behaviors(terms, behaviors, args.behaviors_per_term)
    rows = build_rows(pairs, region=args.region, corpus_path=args.corpus)

    print_summary(rows)

    if args.dry_run:
        print("\n[dry-run] No se escribió en la base.")
        return 0

    conn = get_connection()
    try:
        ensure_metadata_table(conn)
        apply_ingest(conn, rows)
        verify_db(conn)
    finally:
        conn.close()

    print("\n✓ Ingesta aplicada.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
