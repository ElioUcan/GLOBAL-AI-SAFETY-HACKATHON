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

```bash
# Postgres Lizandro en puerto 5433 (evita choque con otras BDs locales)
POSTGRES_PORT=5433 python3 leandro/scripts/ingest_slang_bench.py --dry-run
POSTGRES_PORT=5433 python3 leandro/scripts/ingest_slang_bench.py --apply
```

Repo fuente completo: [Desiler1fro/Webscraping_Jergas_MX](https://github.com/Desiler1fro/Webscraping_Jergas_MX)
