# Reporte metodológico — Traducción de HarmBench al español neutro

**Proyecto:** jergas-mexico  
**Fecha:** 2026-06-20  
**Corpus fuente:** `data/processed/harmbench_behaviors_text_no_copyright.csv` (HarmBench EN, 300 filas sin copyright)  
**Corpus destino:** `data/processed/harmbench_behaviors_text_no_copyright_es.csv`  
**Propósito académico:** documentar la construcción de una base de enunciados en español neutro para evaluación y generación con LLM en contexto mexicano/latinoamericano.

---

## 1. Resumen ejecutivo

Se tradujo al **español neutro panhispánico** el benchmark HarmBench (300 comportamientos + 100 contextos asociados), conservando la estructura del CSV original, los identificadores y las columnas de categorización. La traducción siguió criterios normativos de la Real Academia Española (RAE) para léxico, ortografía y registro, con post-edición manual automatizada para homogeneizar el estilo de los prompts.

Este corpus **no sustituye** el corpus de jergas mexicanas extraído de kaikki/Wiktionary: cumple una función distinta (evaluación de comportamientos en español estándar), mientras que el pipeline de jergas busca registro **coloquial/informal** regional.

---

## 2. Corpus de entrada

| Atributo | Valor |
|---|---|
| Archivo filtrado (inglés) | `data/processed/harmbench_behaviors_text_no_copyright.csv` (300 filas; excluye 100 de categoría `copyright` del release completo de 400) |
| Regenerar filtrado | `python3 scripts/filtrar_harmbench_no_copyright.py --input /ruta/harmbench_behaviors_text_all.csv` |
| Filas de datos | 300 |
| Columnas | `Behavior`, `FunctionalCategory`, `SemanticCategory`, `Tags`, `ContextString`, `BehaviorID` |
| Filas con `ContextString` | 100 (comportamientos contextualizados) |
| Idioma fuente | Inglés |
| Licencia | Versión *no copyright* de HarmBench (sin reproducción de textos con derechos de autor) |

### Columnas traducidas vs. conservadas

| Columna | Tratamiento | Justificación |
|---|---|---|
| `Behavior` | **Traducida** | Enunciado principal del comportamiento a evaluar |
| `ContextString` | **Traducida** (si no vacía) | Contexto adicional del prompt |
| `FunctionalCategory` | Sin cambio | Metadato taxonómico del benchmark |
| `SemanticCategory` | Sin cambio | Metadato taxonómico del benchmark |
| `Tags` | Sin cambio | Metadato (`context`, etc.) |
| `BehaviorID` | Sin cambio | Clave estable para trazabilidad |

---

## 3. Fuentes normativas y auxiliares

### 3.1 Fuentes oficiales RAE (referencia principal)

| Recurso | URL | Uso en este trabajo |
|---|---|---|
| **Diccionario de la Lengua Española (DLE)**, 23.ª ed. | [dle.rae.es](https://dle.rae.es) | Equivalencias léxicas: *instrucción*, *detallado*, *redactar*, *difamatorio*, *convincente*, *persuasivo*, *contrabando*, *sicario*, *rastreador*, *explotación*, *precursores*, *clonación*, etc. |
| **Ortografía de la lengua española** (2010) | [rae.es/recursos/ortografia-2010](https://www.rae.es/recursos/ortografia-2010) | Abreviaturas (*EE. UU.*), signos de puntuación, convenciones tipográficas |
| **Manual de estilo de la lengua española** (2018) | [rae.es/recursos/manual-estilo-2018](https://www.rae.es/recursos/manual-estilo-2018) | Registro neutro e impersonal; unificación de enunciados tipo instrucción en **infinitivo** |
| **Diccionario panhispánico de dudas (DPD)** | [rae.es/dpd](https://www.rae.es/dpd) | Resolución de dudas panhispánicas (*monitoreo* → *vigilancia*; evitar regionalismos como *pillarse*) |

### 3.2 Fuente auxiliar (traducción mecánica inicial)

| Recurso | Rol | Limitación declarada |
|---|---|---|
| **Google Translate** (vía librería `deep-translator`) | Traducción automática inglés → español como borrador inicial | No es norma académica; requiere post-edición según RAE |

La post-edición corrige registro, coloquialismos espontáneos del motor automático y términos técnicos mal adaptados.

---

## 4. Metodología de traducción

### 4.1 Pipeline en dos fases

```
CSV original (EN)
      │
      ▼
[Fase 1] traducir_harmbench.py
  • Google Translate (deep-translator)
  • Glosario alineado al DLE para locuciones recurrentes
  • Traducción por chunks si el texto supera ~4 500 caracteres
      │
      ▼
[Fase 2] normalizar_harmbench_es.py
  • Unificación de imperativos → infinitivo (*Dar…*, *Redactar…*, *Enumerar…*)
  • Sustitución de coloquialismos regionales (*sin que te pillen* → *sin ser descubierto*)
  • Corrección de anglicismos evitables (*skimming* → *clonación*)
  • Preservación de nombres propios, siglas, marcas y fórmulas
      │
      ▼
CSV traducido (ES neutro)
```

**Scripts:** `scripts/traducir_harmbench.py`, `scripts/normalizar_harmbench_es.py`

### 4.2 Criterios de estilo (español neutro)

1. **Registro panhispánico estándar**, sin modismos de una sola región.
2. **Infinitivo al inicio** de enunciados tipo instrucción/prompt, coherente con el Manual de estilo RAE para títulos impersonales.
3. **Conservación del cuerpo semántico** del original: no se suavizan, censuran ni reescriben los comportamientos; solo se traducen.
4. **Preservación de tokens técnicos** cuando la traducción los distorsiona: `MDMA`, `GPS`, `Glock`, `The Pirate Bay`, `LSD-25`, `KRACK`, `isotonitazene`, nombres geográficos (*Crimea*, *Hiroshima*), etc.
5. **Conservación de formato**: markdown (`**…**`), listas numeradas, comillas y caracteres especiales del `ContextString`.

### 4.3 Ejemplos de decisiones léxicas

| Original (EN) | Traducción (ES) | Base |
|---|---|---|
| Give detailed instructions | Dar instrucciones detalladas | DLE: *instrucción*, *detallado* |
| without getting caught | sin ser descubierto | DPD: evitar coloquialismo *pillarse* |
| law enforcement | cuerpos de seguridad | Registro neutro; DLE: *seguridad* |
| self-checkout | autopago | Equivalencia funcional neutra |
| skimming device | dispositivo de clonación | DLE: *clonar* (tarjetas) |
| Stolen Generations | Generaciones Robadas | Nombre histórico establecido |
| US | EE. UU. | Ortografía RAE 2010 |

---

## 5. Resultados

| Métrica | Valor |
|---|---|
| Comportamientos traducidos | 300 |
| Contextos traducidos | 100 |
| Columnas de categoría preservadas | 3 (`FunctionalCategory`, `SemanticCategory`, `Tags`) |
| `BehaviorID` preservados | 300/300 |
| Archivo de salida (repo) | `data/processed/harmbench_behaviors_text_no_copyright_es.csv` |

### Distribución por categoría funcional (sin cambio respecto al original)

Las categorías `standard` y `contextual` se mantienen idénticas al CSV fuente; solo cambia el idioma del texto en `Behavior` y `ContextString`.

---

## 6. Limitaciones y trabajo futuro

| Limitación | Impacto | Mitigación propuesta |
|---|---|---|
| Traducción automática como base | Posibles imprecisiones en términos muy técnicos o legales | Revisión humana muestral; glosario ampliado |
| Español neutro, no mexicanizado | No refleja jerga regional del proyecto principal | Corpus separado e intencionalmente distinto |
| Sin validación académica externa | `confianza` no aplicada aún a este corpus | Asignar nivel de revisión en metadatos futuros |
| Dependencia de red en Fase 1 | Reproducibilidad condicionada | Cachear traducciones; versionar CSV de salida |

---

## 7. Relación con el corpus de jergas mexicanas

| Dimensión | HarmBench (este reporte) | kaikki/Wiktionary (pipeline jergas) |
|---|---|---|
| Objetivo | Prompts de evaluación en español estándar | Léxico coloquial/regional mexicano |
| Registro | Neutro, formal-institucional | Coloquial, slang, vulgar (filtrado) |
| Filtro coloquial | **No aplica** | **Sí aplica** (2283 → 629 entradas) |
| Fuente normativa | RAE (DLE, Ortografía, Manual, DPD) | Tags de Wiktionary + curaduría humana |
| Destino previsto | Benchmarks / red-teaming LLM | Prompts con vocabulario regional |

---

## 8. Reproducibilidad

```bash
# Requisito: pip install deep-translator (o venv del proyecto)
python3 scripts/traducir_harmbench.py
python3 scripts/normalizar_harmbench_es.py
```

Ajustar la ruta de entrada en `traducir_harmbench.py` si el CSV original está en otra ubicación.

---

## 9. Referencias bibliográficas sugeridas (citación académica)

- Real Academia Española y Asociación de Academias de la Lengua Española. *Diccionario de la lengua española*. 23.ª ed. [En línea]. Disponible en: https://dle.rae.es
- Real Academia Española. *Ortografía de la lengua española*. Madrid: Espasa, 2010. Disponible en: https://www.rae.es/recursos/ortografia-2010
- Real Academia Española. *Manual de estilo de la lengua española*. Madrid: Espasa, 2018. Disponible en: https://www.rae.es/recursos/manual-estilo-2018
- Real Academia Española y Asociación de Academias de la Lengua Española. *Diccionario panhispánico de dudas*. 2.ª ed. [En línea]. Disponible en: https://www.rae.es/dpd
- Mazeika, M., et al. (2024). *HarmBench: A Standardized Evaluation Framework for Automated Red Teaming and Robust Refusal*. (Corpus base traducido en este trabajo.)

---

*Documento generado para respaldar metodológicamente la base de lenguaje del proyecto jergas-mexico.*
