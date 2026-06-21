# Entrega — Leandro (jergas MX + HarmBench ES)

Artefactos del proyecto **Webscraping_Jergas_MX** para el hackathon.

## Contenido

| Carpeta | Archivos |
|---|---|
| `datasets/originales/` | 3 JSON congelados (605 + 22 + 627) + `.CONGELADO` |
| `datasets/sin_significado/` | Mismos 3 JSON sin campos de glosa/significado |
| `harmbench/` | HarmBench EN y ES (300 behaviors, sin copyright) |
| `scripts/` | Ingesta idempotente `slang_bench.jerga` v1.1.0 + SQL `jerga_metadata` |
| `docs/` | Descripción de datasets, reportes, integración slang_bench |

## Documentación

- [`docs/DATASETS.md`](docs/DATASETS.md) — qué contiene cada JSON y variación por fuentes
- [`docs/REPORTE_LINEA_C_REDDIT.md`](docs/REPORTE_LINEA_C_REDDIT.md) — piloto Reddit y curaduría
- [`docs/REPORTE_TRADUCCION_HARMBENCH.md`](docs/REPORTE_TRADUCCION_HARMBENCH.md) — metodología HarmBench ES
- [`docs/CONSIDERACIONES_INTEGRACION.md`](docs/CONSIDERACIONES_INTEGRACION.md) — ingesta corpus → `slang_bench` (PR hacia rama Lizandro)

## Ingesta slang_bench

Guía completa paso a paso (clon limpio, puerto, schema Lizandro, verificación):
[`docs/CONSIDERACIONES_INTEGRACION.md`](docs/CONSIDERACIONES_INTEGRACION.md) §5.

```bash
python3 -m pip install -r leandro/requirements.txt
export POSTGRES_PORT=5433   # env var; no editar compose.yml
POSTGRES_PORT=$POSTGRES_PORT docker compose up -d --build postgres
python3 leandro/scripts/ingest_slang_bench.py --dry-run --min-confianza 2 --behaviors-per-term 3
POSTGRES_PORT=$POSTGRES_PORT python3 leandro/scripts/ingest_slang_bench.py --apply --min-confianza 2 --behaviors-per-term 3
POSTGRES_PORT=$POSTGRES_PORT python3 leandro/scripts/ingest_slang_bench.py --verify-only
```

Repo fuente completo: [Desiler1fro/Webscraping_Jergas_MX](https://github.com/Desiler1fro/Webscraping_Jergas_MX)
