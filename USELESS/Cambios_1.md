# Yucatan Slang Jailbreak Benchmark — Cambios 1

Benchmark de red-teaming para medir si los filtros de seguridad de LLMs resisten prompts adversarios escritos con jerga yucateca/mexicana. El flujo completo es **Attacker → Target → Judge → Storage**, con resultados consultables en PostgreSQL y visualizados en Grafana.

Hay **dos formas de ejecutar el pipeline**: el workflow de **n8n** (orquestación visual) y la **CLI en Python** (`attacker/`), pensada para pruebas más rápidas sin depender del editor de n8n. Ambas escriben en las mismas tablas de PostgreSQL.

## Tecnologías

![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Grafana](https://img.shields.io/badge/Grafana-F46800?style=for-the-badge&logo=grafana&logoColor=white)
![n8n](https://img.shields.io/badge/n8n-EA4B71?style=for-the-badge&logo=n8n&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2CA5E0?style=for-the-badge&logo=docker&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![NVIDIA NIM](https://img.shields.io/badge/NVIDIA%20NIM-76B900?style=for-the-badge&logo=nvidia&logoColor=white)

---

## Estructura del repositorio

```
GLOBAL-AI-SAFETY-HACKATHON/
├── attacker/                  # CLI Python — mismo pipeline que n8n, para testing rápido
│   ├── main.py                # Entry point del workflow completo
│   ├── techniques.py          # Registro de las 7 técnicas de ataque
│   └── requirements.txt       # Dependencias Python
├── docker/
│   ├── postgres/              # Imagen + scripts de inicialización de la BD
│   ├── n8n/                   # Imagen de n8n con task runners habilitados
│   └── grafana/               # Imagen + provisioning de datasource/dashboards
├── grafana/                   # Dashboards JSON (vacío — pendiente de Lizandro y Fer)
├── scripts/                   # Utilidades (generación de paper/pitch)
├── compose.yml                # Levanta postgres, n8n y grafana
├── .env.example               # Plantilla de variables de entorno
├── AGENTS.md                  # Especificación de cada agente (prompts, modelos, esquemas)
├── CHANGELOG.md               # Historial de cambios del proyecto
├── MISSING.md                 # Checklist de lo que falta por completar
└── Yucatan Slang Jailbreak Benchmark.json   # Workflow de n8n para importar
```

| Archivo / carpeta | Propósito |
|---|---|
| `.env` | Variables de entorno reales (no se sube a git). Copiar desde `.env.example`. |
| `.env.example` | Plantilla con todas las variables necesarias. Rellenar `NVIDIA_API_KEY` y cambiar contraseñas a gusto; **no cambiar los puertos**. |
| `.gitignore` | Archivos que git ignora al hacer push (`.env`, cachés, etc.). |
| `AGENTS.md` | Documentación actualizada de los cuatro agentes y cómo encadenan. |
| `CHANGELOG.md` | Registro de cambios — revisar qué hizo Elio, notas y mejoras. |
| `MISSING.md` | Checklist detallado de tareas pendientes con referencias a archivos. |
| `webscrapper.py` | Placeholder del scraper futuro de jerga (aún sin implementar). |

---

## Inicio rápido

### 1. Configurar entorno

```bash
cp .env.example .env
# Editar .env: NVIDIA_API_KEY, contraseñas, etc.
```

### 2. Levantar servicios

```bash
docker compose up -d --build
```

### 3. Acceder a los servicios

| Servicio | URL | Credenciales |
|---|---|---|
| n8n (editor de workflows) | http://localhost:5678 | — |
| Grafana (dashboards) | http://localhost:3000 | `admin` / `admin` |
| PostgreSQL | `localhost:5432` | user: `admin`, db: `slang_bench` |

Para detener: `docker compose down`  
Para reiniciar desde cero (borra volúmenes): `docker compose down -v`

---

## Carpeta `attacker/` — CLI Python

Implementación en código del workflow de n8n. Útil para iterar rápido, hacer dry-runs y validar el pipeline sin abrir n8n. **No reemplaza** el workflow visual; es un complemento opcional.

### Pipeline (`main.py`)

```
Fetch Jerga → Attacker → Target → Regex pre-filter → Judge → Storage
```

| Componente | Descripción |
|---|---|
| **Modelos** | Constantes al inicio de `main.py` (`ATTACKER_MODEL`, `JUDGE_MODEL`, `DEFAULT_TARGET_MODEL`). Los slugs de NVIDIA NIM **aún no están definidos al 100%** — revisar y ajustar antes de correr en producción. |
| **Attacker system prompt** | Genera prompts adversarios con jerga. Revisar y enriquecer con más contexto e investigación (ver `AGENTS.md`). |
| **Judge system prompt** | Evalúa si hubo jailbreak. Mismo pendiente: validar redacción y schema de salida JSON. |
| **Regex pre-filter** | Expresiones/palabras clave (`HARM_KEYWORDS`) que detectan daño obvio en la respuesta del Target. Si hay match, **se omite la llamada al Judge** y se ahorran tokens. Ampliar la lista con las keywords más comunes por categoría. |
| **PAIR loop** (`pair_refine`) | Ataque multi-turno: Attacker refina según feedback del Judge. Máximo 5 rondas; se detiene si `confidence ≥ 0.8`. |
| **Base de datos** | `get_connection()` y `store_result()` escriben en PostgreSQL. Requiere tablas `jerga` y `results` (ver sección Database). |
| **APIs** | Todas las llamadas LLM pasan por LiteLLM → NVIDIA NIM con `NVIDIA_API_KEY`. |

### Instalación y uso

```bash
pip install -r attacker/requirements.txt

# Variables (desde .env o export manual)
export NVIDIA_API_KEY=tu-clave-nvidia
export POSTGRES_HOST=localhost   # los contenedores usan "postgres" internamente
export POSTGRES_PORT=5432
export POSTGRES_USER=admin
export POSTGRES_PASSWORD=changeme
export POSTGRES_DB=slang_bench

# 100 iteraciones, rotando las 7 técnicas (default)
python attacker/main.py --limit 100

# Técnica y modelo específicos
python attacker/main.py \
  --target nvidia_nim/meta/llama-3.1-8b-instruct \
  --technique roleplay_wrap \
  --limit 100

# Dry-run: planifica sin llamar APIs ni escribir en BD
python attacker/main.py --limit 8 --dry-run
```

| Flag | Descripción | Default |
|---|---|---|
| `--target` | Modelo Target (slug NVIDIA NIM) | `nvidia_nim/meta/llama-3.1-8b-instruct` |
| `--technique` | Técnica fija; omitir para rotar las 7 | rotación |
| `--limit` | Número de iteraciones | `100` |
| `--dry-run` | Solo imprime el plan; sin LLM ni BD | off |

### Técnicas de ataque (`techniques.py`)

Las siete técnicas están definidas en `VALID_TECHNIQUES` y documentadas en `AGENTS.md`:

`translation_transfer` · `semantic_obfuscation` · `crescendo` · `codeswitching` · `roleplay_wrap` · `manyshot_slang` · `pair_refine`

> **JSON válido:** tanto `main.py` como n8n deben devolver JSON bien formado (JSON-V) en las salidas del Judge y en cualquier campo que PostgreSQL persista como JSON/JSONB.

### Dependencias (`requirements.txt`)

- `litellm` — cliente unificado para NVIDIA NIM
- `psycopg2-binary` — conexión a PostgreSQL
- `python-dotenv` — carga opcional de `.env` en runs locales

---

## Carpeta `docker/` — Servicios

Los Dockerfiles y provisioning definen los tres servicios del stack:

| Servicio | Carpeta | Función |
|---|---|---|
| **PostgreSQL** | `docker/postgres/` | Almacena el corpus de jerga (`jerga`) y los resultados de ataques (`results`). Los scripts `*.sql` en `docker/postgres/init/` se ejecutan solo en el **primer arranque** del volumen. |
| **n8n** | `docker/n8n/` | Orquesta el pipeline Attacker → Target → Judge → Storage. Task runners habilitados para nodos Python. |
| **Grafana** | `docker/grafana/` | Dashboards conectados a PostgreSQL. El provisioning de datasource está en `docker/grafana/provisioning/`. |

### Base de datos (pendiente de crear)

Los scripts de inicialización **aún no existen** — hay que crearlos desde cero:

| Script | Contenido |
|---|---|
| `docker/postgres/init/01-schema.sql` | Tablas `jerga` y `results` con columnas, índices y tipos compatibles con JSON válido donde aplique. |
| `docker/postgres/init/02-seed-jerga.sql` | Datos sintéticos de prueba (≥ 10–20 filas). Si el workflow funciona, migrar datos reales al schema definitivo. |

Tras crear los scripts: `docker compose down -v && docker compose up -d --build`

Detalle de columnas y referencias: ver `MISSING.md` sección 1 y `AGENTS.md`.

---

## Carpeta `grafana/` — Dashboards

Actualmente vacía (solo `.gitkeep`). **Lizandro y Fer** deben colocar aquí los archivos JSON de dashboards; Grafana los carga automáticamente vía el provider en `docker/grafana/provisioning/dashboards/dashboards.yml`.

Dashboards esperados (queries en `AGENTS.md`):

1. Tasa de éxito por `target_model`
2. Tasa de éxito por `attack_technique`
3. Categorías de daño más vulnerables (`harm_category`)

No olvidar `docker compose up` después de añadir dashboards.

---

## Workflow n8n — `Yucatan Slang Jailbreak Benchmark.json`

### Importar

1. Abrir n8n → http://localhost:5678
2. Ir a **Workflows** → **Import from file**
3. Subir `Yucatan Slang Jailbreak Benchmark.json`
4. Configurar credenciales en los nodos con símbolo de advertencia (⚠):
   - **NVIDIA API key** (Attacker, Target, Judge)
   - **PostgreSQL** (Fetch Jerga, Store Result)

### Editar system prompts y regex en n8n

> **Importante:** los system prompts, regex y lógica embebida en el JSON **no se sincronizan solos** con `attacker/main.py`. Hay que editarlos manualmente en n8n:
>
> 1. Doble clic en el nodo (Attacker, Judge, Regex Pre-filter)
> 2. **Open** o **Inspect** para ver/editar el prompt o código
> 3. Mantener paridad con `AGENTS.md` y `attacker/main.py`

Cualquier cambio en `attacker/main.py` (prompts, `HARM_KEYWORDS`, regex) **debe replicarse** en los nodos equivalentes del workflow n8n.

### Pendientes del workflow

El workflow está **casi completo** pero requiere trabajo adicional (detalle en `MISSING.md` sección 3):

- Corregir el cableado del loop de batch (`splitInBatches` v3)
- Rotación de técnicas y modelos target por iteración
- Implementar el PAIR loop (`pair_refine`) — hoy es solo una nota sticky
- Ampliar el batch a **120 prompts** (configurable vía `batch_iterations`)
- Añadir **triggers automáticos** (cron/webhook) en lugar de ejecución manual
- Validaciones y manejo de errores robusto (`continueOnFail`, reintentos)
- Credenciales y checks de integración

Se recomienda que **dos personas** apoyen a Karol en la configuración de n8n — es un proceso pesado.

Tras terminar cambios en n8n: exportar el workflow, descargar y renombrar la nueva versión del JSON en el repo.

---

## Formato JSON-V (JSON válido)

PostgreSQL acepta JSON/JSONB solo si el payload es **JSON válido** (JSON-V). Esto aplica a:

- Salida del Judge (`jailbreak_success`, `confidence`, `severity`, `reasoning`, etc.)
- Cualquier campo JSON persistido en `results`
- Outputs de nodos n8n que escriben en la base de datos

Validar que `main.py` y n8n produzcan JSON parseable antes de insertar.

---

## Documentación de referencia

| Documento | Para qué sirve |
|---|---|
| [`AGENTS.md`](AGENTS.md) | Especificación completa de Attacker, Target, Judge y Storage: prompts, modelos, técnicas, métricas SQL. |
| [`CHANGELOG.md`](CHANGELOG.md) | Historial de versiones y cambios. **Registrar cada push significativo aquí.** |
| [`MISSING.md`](MISSING.md) | Checklist accionable de todo lo pendiente. Si algo no está contemplado, agregarlo ahí. |

---

## Advertencias

### No hacer push directo a `main`

Elio creó un backup en GitHub (tags), pero **tengan cuidado al pushear a `main`**. Trabajar en ramas feature y abrir PRs. El backup más reciente está en GitHub → **Tags**.

### Sincronización Python ↔ n8n

Los cambios en `attacker/main.py` no se reflejan automáticamente en n8n. Cualquier modificación a prompts, regex o lógica debe aplicarse en **ambos lugares**.

---

## Recomendaciones para el equipo

1. **CHANGELOG** — documentar cada push o entrega relevante en `CHANGELOG.md`
2. **Cursor** — usar Cursor para iterar en código, prompts y documentación
3. **MISSING.md** — marcar tareas completadas y agregar nuevas pendientes
4. **Dry-run primero** — `python attacker/main.py --dry-run` no requiere API key ni BD
5. **Paridad de keywords** — mantener `HARM_KEYWORDS` idénticas en Python y en el nodo Regex de n8n

---

## Validación end-to-end (cuando todo esté listo)

1. `docker compose up -d --build` — confirmar que Postgres creó tablas y seed
2. `python attacker/main.py --limit 5` con `NVIDIA_API_KEY` real — confirmar filas en `results`
3. Importar y ejecutar el workflow n8n — confirmar que el batch itera correctamente
4. Abrir Grafana — confirmar que los dashboards muestran datos reales
