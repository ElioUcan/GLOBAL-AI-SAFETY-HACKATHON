# Reporte: Línea C — Piloto Reddit y datasets congelados

_2026-06-21. Estado: **cerrada** (curaduría completada)._

Documento de referencia del trabajo Reddit. Estado operativo resumido en [`ESTADO_PROYECTO.md`](../ESTADO_PROYECTO.md).

---

## Resumen ejecutivo

| Etapa | Resultado |
|---|---|
| Propuesta metodológica | [`metodologia_reddit_propuesta.md`](metodologia_reddit_propuesta.md), [`web_scraper.pdf`](web_scraper.pdf) |
| Implementación | `extraer_reddit.py`, `combinar_datasets.py`, `preparar_cola_reddit.py`, `promover_reddit_curado.py`, `exportar_corpus_prompt.py` |
| Ingesta | 15 comentarios (fixture; Reddit 403 sin OAuth) |
| Candidatos extraídos | 37 → 22 nuevos vs 605 + 15 duplicados |
| Curaduría | 15 rechazados (duplicados) + 22 aprobados (`confianza=2`) |
| **Datasets congelados** | 3 JSON en `data/processed/datasets/` — **inamovibles** |

---

## Datasets congelados (inamovibles)

Marcador: `data/processed/datasets/.CONGELADO`

| Archivo | Filas | Contenido |
|---|---:|---|
| `dataset_original_605.json` | 605 | Copia idéntica de `jergas_corpus.json` al momento del cierre |
| `dataset_nuevo_piloto.json` | 22 | L lemmas Reddit aprobados en curaduría |
| `dataset_combinado.json` | 627 | 605 estables + 22 curados; sección `rechazados_reddit` (15) |

### Regla de inmutabilidad

- **No editar, regenerar ni sobrescribir** estos tres archivos.
- Scripts (`combinar_datasets.py`, `extraer_reddit.py`) abortan si intentan escribirlos (salvo `--force`).
- Iteraciones futuras → `data/processed/datasets/iteraciones/<nombre>/`.
- El canónico Línea A (`jergas_corpus.json`, 605 filas) también permanece intacto.

### Artefactos derivados (no congelados, regenerables)

| Archivo | Filas | Uso |
|---|---:|---|
| `jergas_corpus_extendido.json` | 627 | 605 + 22 Reddit curados |
| `corpus_prompt_produccion.json` | 525 | Prompts LLM (`confianza ≥ 2`) |
| `corpus_prompt.json` | 627 | Sandbox (`confianza ≥ 1`) |
| `cola_revision_reddit_resuelta.json` | — | Auditoría de curaduría |

---

## Pipeline ejecutado

```
Reddit/fixture → extraer_reddit.py → dataset_nuevo_piloto (v0.1, 37 candidatos)
       → combinar_datasets.py → dataset_combinado (v0.1, experimental)
       → preparar_cola_reddit.py → cola_revision_reddit.json
       → revisión humana (15 auto-rechazados + 22 aprobados)
       → promover_reddit_curado.py --aplicar
       → jergas_corpus_extendido.json + datasets v0.2.0-curado (CONGELADOS)
       → exportar_corpus_prompt.py
```

---

## Curaduría (2026-06-21)

### Rechazados (15) — duplicados del corpus 605

*a toda madre*, *chafa*, *chido*, *compa*, *güey*, *jale*, *la neta*, *naco*, *no mames*, *padre*, *qué pedo*, *rola*, *simón*, *vato*, *wey*

### Aprobados (22) — `confianza=2`

*a poco*, *aguas*, *alberca*, *carnalito*, *chalecito*, *chambita*, *chincualo*, *chismoso*, *faena*, *feria*, *fregado*, *fuchi*, *gandalla*, *gandallita*, *la banda*, *malandro*, *morra*, *morras*, *morros*, *órale*, *pachanga*, *que show*

---

## Decisiones de diseño

1. **No jailbreaks automáticos** — el glosario no alimenta reescritura HarmBench (ver propuesta, Cap. 6).
2. **Unión conservadora** — duplicados del 605 no se fusionan; se rechazan.
3. **Postgres sin sync** — BD sigue en 605 hasta decisión explícita de migrar desde extendido.
4. **Fixture vs Reddit vivo** — primera corrida usó fixture; PRAW pendiente con credenciales.

---

## Limitaciones conocidas

- Extracción heurística (Ollama no disponible en corrida).
- Sin atribución regional fina (todo General México).
- `morra`/`morras` aprobados como lemas separados (ajuste fino posterior opcional en iteración paralela).
- Significados Reddit en español coloquial; algunos glosas del 605 siguen en inglés (kaikki).

---

## Comandos (solo iteraciones nuevas)

```bash
# Nueva corrida — NO toca datasets congelados
python3 scripts/extraer_reddit.py --salida-dir data/processed/datasets/iteraciones/mi_corrida/
python3 scripts/combinar_datasets.py --salida-dir data/processed/datasets/iteraciones/mi_corrida/

# Consumo producción (desde extendido, no desde combinado congelado)
python3 scripts/exportar_corpus_prompt.py
```

---

## Referencias

- Propuesta original: [`metodologia_reddit_propuesta.md`](metodologia_reddit_propuesta.md)
- Estado consolidado: [`ESTADO_PROYECTO.md`](../ESTADO_PROYECTO.md)
