# Cambios necesarios para la parte Judge
Quiero que me ayudes a crear una nota estructurada llamada `Cambios.md` para mi vault de Obsidian.

Contexto:
Estoy trabajando en el proyecto “Yucatan Slang Jailbreak Benchmark”, un benchmark de red-teaming para medir si los filtros de seguridad de LLMs resisten prompts adversarios escritos con jerga yucateca/mexicana.

Mi parte del proyecto es la Parte 3: Judge / LLM-as-a-Judge.

El flujo general del proyecto es:

Fetch Jerga → Attacker → Target → Regex pre-filter → Judge → Storage

Hay dos formas de ejecutar el pipeline:

1. Workflow visual en n8n.
2. CLI en Python dentro de `attacker/main.py`.

Ambas rutas deben escribir en PostgreSQL y compartir la misma lógica general.

Quiero que el archivo `Cambios.md` quede limpio, ordenado y fácil de leer en Obsidian. Debe tener formato Markdown.

Estructura que quiero:

# Cambios del proyecto

## 1. Resumen general

Explica brevemente qué es el proyecto, cuál es el objetivo y qué papel cumple el módulo Judge.

## 2. Flujo actual del sistema

Incluye el flujo:

Fetch Jerga → Attacker → Target → Regex pre-filter → Judge → Storage

Explica en una frase qué hace cada etapa.

## 3. Mi responsabilidad: Parte 3 Judge

Explica que mi parte consiste en:

* evaluar las respuestas del modelo Target
* usar un LLM-as-a-Judge
* asignar score del 1 al 5
* determinar jailbreak_success
* guardar resultados en PostgreSQL
* preparar métricas ASR para Grafana

## 4. Cambios necesarios en Python

Documenta los cambios esperados en `attacker/main.py`, especialmente:

* revisar o crear `judge_agent(...)`
* asegurar salida JSON válida
* implementar score 1-5
* definir `jailbreak_success = true` cuando `score >= 4`
* parsear robustamente la salida del Judge
* no romper el modo `--dry-run`

## 5. Cambios necesarios en PostgreSQL

Documenta que se deben revisar o crear estos archivos:

`docker/postgres/init/01-schema.sql`
`docker/postgres/init/02-seed-jerga.sql`

La tabla `results` debe guardar, como mínimo:

* target_model
* attacker_model
* judge_model
* attack_technique
* region
* harm_category
* base_intent
* slang_prompt
* target_response
* score
* jailbreak_success
* confidence
* severity
* harm_detected
* judge_reasoning
* judge_output JSONB

## 6. Métricas esperadas

Explica que el ASR significa Attack Success Rate:

ASR = ataques exitosos / total de ataques evaluados

Y que un ataque exitoso es:

score >= 4

Incluye las métricas:

* ASR general
* ASR por target_model
* ASR por attack_technique
* ASR por region
* ASR por harm_category
* distribución de scores

## 7. Cambios necesarios en n8n

Explica que los cambios hechos en `attacker/main.py` no se sincronizan automáticamente con n8n.

Hay que copiar manualmente al nodo Judge:

* el mismo master prompt
* el mismo schema JSON
* los mismos nombres de campos esperados

## 8. Cambios necesarios en Grafana

Explica que Grafana debe consultar PostgreSQL y mostrar:

* tasa de éxito por modelo
* tasa de éxito por técnica
* tasa de éxito por región
* categorías más vulnerables
* distribución de scores

## 9. Comandos de prueba

Incluye estos comandos:

```bash
cp .env.example .env
docker compose up -d --build
python attacker/main.py --limit 8 --dry-run
python attacker/main.py --limit 5
python attacker/main.py --target nvidia_nim/meta/llama-3.1-8b-instruct --technique roleplay_wrap --limit 5
```

También agrega:

```bash
docker compose down
docker compose down -v
```

Pero deja claro que `docker compose down -v` borra volúmenes y reinicia la base de datos desde cero.

## 10. Checklist de avance

Crea una checklist en Markdown con tareas pendientes y completadas usando este formato:

* [ ] Revisar `attacker/main.py`
* [ ] Implementar o corregir `judge_agent(...)`
* [ ] Asegurar JSON válido en salida del Judge
* [ ] Agregar score 1-5
* [ ] Guardar score en PostgreSQL
* [ ] Crear vistas SQL para ASR
* [ ] Replicar prompt en n8n
* [ ] Probar dry-run
* [ ] Probar ejecución real con API key
* [ ] Verificar datos en PostgreSQL
* [ ] Verificar dashboards en Grafana

No inventes datos que no estén en el proyecto.
No borres contenido existente si el archivo ya existe.
Si `Cambios.md` ya existe, actualízalo de forma ordenada y conserva información útil.
