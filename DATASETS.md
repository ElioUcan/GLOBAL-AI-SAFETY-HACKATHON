# Datasets del proyecto

Descripción del **contenido** y **variación por fuentes** de cada artefacto JSON.  
Los originales congelados están en [`data/processed/datasets/`](../data/processed/datasets/.CONGELADO).  
Copias sin glosas/definiciones: [`sin_significado/`](../data/processed/datasets/sin_significado/).

---

## Congelados (con significado)

### `dataset_original_605.json`

- **Qué es:** Snapshot del corpus canónico Línea A en el momento del cierre de Línea C.
- **Filas:** 605 lemas.
- **Fuentes:** kaikki.org (Wiktionary parseado), DEM, AML breve — según campo `fuentes` por entrada.
- **Contenido por entrada:** término, significado (glosa), tags de registro/región, `pos`, región/estado, `confianza` (1–3), variantes en `fuentes_detalle` cuando aplica.
- **Variación respecto a los otros:** Es el subconjunto **estable académico+lexicográfico**; no incluye Reddit ni metadatos `reddit{}`.

### `dataset_nuevo_piloto.json`

- **Qué es:** Solo los 22 lemas Reddit **aprobados** en curaduría (Línea C).
- **Filas:** 22.
- **Fuente única:** `reddit` (comentarios estilo r/mexico; corrida inicial con fixture).
- **Contenido por entrada:** término, significado curado, `ejemplo_uso` (fragmento del comentario), bloque `reddit` (subreddit, permalink, fecha, score, método de extracción), `confianza=2`, región General México.
- **Variación respecto a los otros:** Es el único archivo **100 % Reddit** y el más reciente en registro digital; no comparte pipeline DEM/AML.

### `dataset_combinado.json`

- **Qué es:** Unión documentada del 605 estable + 22 Reddit curados.
- **Filas:** 627 en `entradas`; 15 ítems en `rechazados_reddit` (duplicados del 605 no integrados).
- **Fuentes mezcladas:** entradas con `procedencia=corpus_estable` (kaikki/dem/aml) + `procedencia=reddit_curado`.
- **Contenido extra:** `metadata.fusion` (conteos, método), `duplicados_piloto` / `rechazados_reddit` con contexto Reddit de términos ya existentes en el 605.
- **Variación respecto a los otros:** Es el **único** que contiene ambas procedencias y la auditoría de rechazados; esquema heterogéneo (p. ej. `fuentes_detalle` solo en estables, `reddit{}` solo en piloto).

---

## Derivados sin significado (`sin_significado/`)

Misma estructura que los congelados, pero **sin** campos `significado`, `significado_*` ni glosas en `fuentes_detalle`.  
Útil cuando solo se necesitan lemas, procedencia, región y trazabilidad de fuente.

| Archivo | Deriva de |
|---|---|
| `dataset_original_605_sin_significado.json` | `dataset_original_605.json` |
| `dataset_nuevo_piloto_sin_significado.json` | `dataset_nuevo_piloto.json` |
| `dataset_combinado_sin_significado.json` | `dataset_combinado.json` |

Regenerar:

```bash
python3 scripts/generar_datasets_sin_significado.py
```

---

## Relación entre archivos

```
jergas_corpus.json (605, canónico BD)
        │
        ├── dataset_original_605.json          ← copia congelada
        │
dataset_nuevo_piloto.json (22 Reddit)
        │
        └── dataset_combinado.json             ← 605 + 22 (+ rechazados)
                    │
                    └── sin_significado/*      ← mismos, sin glosas
```

---

## Otros JSON relacionados (no congelados)

| Archivo | Contenido | Fuentes |
|---|---|---|
| `jergas_corpus_extendido.json` | 627 lemas en formato corpus (605+22) | Igual que combinado, sin wrapper de fusión |
| `corpus_prompt_produccion.json` | 525 entradas compactas (`t`, `s`, …) | Derivado de extendido; campo `s` = significado |

Estos no tienen copia `sin_significado` automática; pedir regeneración si se necesitan.
