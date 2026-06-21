# Contexto Técnico del Proyecto

## Yucatán Slang Jailbreak Benchmark

### Estado del proyecto (Junio 2026)

---

# Objetivo del proyecto

El proyecto busca construir un benchmark completamente automatizado para evaluar la robustez de modelos LLM frente a intentos de jailbreak utilizando jergas regionales de Yucatán.

La idea principal es medir qué tan efectivo es un prompt adversarial construido alrededor de expresiones coloquiales para inducir respuestas inseguras en distintos modelos.

Todo el proceso se automatiza mediante n8n para poder ejecutar cientos de pruebas de manera repetible.

---

# Arquitectura general

Actualmente la arquitectura del benchmark es la siguiente:

```
Attack Config
        │
        ▼
Generate Batch Items
        │
        ▼
Loop Batch
        │
        ▼
Fetch Jerga (PostgreSQL)
        │
        ▼
Attacker Agent
        │
        ▼
Extract Adversarial Prompt
        │
        ▼
Target LLM (NVIDIA NIM)
        │
        ▼
Extract Target Response
        │
        ▼
Regex Pre-filter
        │
        ▼
Skip Judge?
      ┌───────┐
      │       │
      ▼       ▼
Regex      Judge Agent
 Verdict        │
      │          ▼
      └────►Normalize Output
                   │
                   ▼
              Store Result
                   │
                   ▼
               PostgreSQL
                   │
                   ▼
                Grafana
```

---

# Tecnologías utilizadas

* n8n
* PostgreSQL
* NVIDIA NIM
* Grafana
* Docker Compose
* OpenClaw
* Ollama
* Firejail

---

# Objetivo de cada componente

## PostgreSQL

Contiene dos tablas principales.

### jerga

Almacena:

* término
* significado
* categoría de daño
* región
* ejemplos

Cada ejecución obtiene una jerga aleatoria.

---

### results

Guarda:

* prompt generado
* respuesta del Target
* resultado del Judge
* score
* severidad
* técnica utilizada
* modelo objetivo
* timestamp

Grafana consume esta tabla.

---

## Attacker Agent

Responsabilidad:

Generar automáticamente un prompt adversarial usando:

* la jerga obtenida
* la técnica de jailbreak
* el modelo objetivo

El agente utiliza un modelo NVIDIA Nemotron (Llama 405B).

---

## Target LLM

Responsabilidad:

Enviar el prompt generado al modelo objetivo mediante NVIDIA NIM.

Actualmente se usan modelos como:

* meta/llama-3.1-8b-instruct

La llamada se realiza vía HTTP Request.

---

## Regex Pre-filter

Responsabilidad:

Evitar enviar respuestas triviales al Judge.

Si una respuesta contiene patrones claramente peligrosos se marca inmediatamente como jailbreak exitoso.

Con esto:

* se reduce costo
* se reduce latencia
* el Judge procesa únicamente casos ambiguos

---

## Judge Agent

Evalúa:

* score
* confianza
* severidad
* explicación
* éxito del jailbreak

---

## Store Result

Inserta toda la ejecución en PostgreSQL.

Posteriormente Grafana construye dashboards.

---

# Trabajo realizado durante la configuración

## 1. OpenClaw

Inicialmente OpenClaw estaba instalado fuera del sandbox.

Se decidió aislar completamente el agente.

Se creó:

```
/home/karol/ai-sandbox
```

Posteriormente OpenClaw quedó configurado para trabajar usando:

```
HOME=/home/karol/ai-sandbox
```

Beneficios:

* configuración aislada
* memoria independiente
* hooks independientes
* workspace independiente

---

## 2. Firejail

Se configuró Firejail para ejecutar OpenClaw.

Objetivo:

Evitar que el agente tenga acceso completo al sistema.

El workspace quedó en:

```
~/ai-sandbox/openclaw/workspace
```

---

## 3. PATH dentro del sandbox

Inicialmente OpenClaw no era encontrado.

Se creó:

```
~/.npm-global
```

Se configuró:

```
npm config set prefix ~/.npm-global
```

Y posteriormente:

```
PATH=$HOME/.npm-global/bin
```

Con esto OpenClaw pudo ejecutarse normalmente.

---

## 4. Gateway

Durante la instalación apareció:

```
Gateway install failed
```

Se descubrió que el servicio systemd simplemente no existe.

No afecta el funcionamiento manual del agente.

Se dejó pendiente únicamente el Gateway persistente.

---

# Configuración de n8n

Se resolvieron múltiples problemas.

---

## Problema 1

### Credenciales PostgreSQL

Inicialmente Fetch Jerga no podía conectarse.

Se configuró correctamente:

Host

```
localhost
```

Database

```
slang_bench
```

Usuario

```
admin
```

Contraseña

desde .env

Resultado:

Fetch Jerga comenzó a funcionar.

---

## Problema 2

### Credenciales NVIDIA

Se creó correctamente la credencial NVIDIA NIM.

Se probaron:

* API Key
* Base URL

La conexión quedó validada.

---

## Problema 3

### model.includes is not a function

El nodo AI tenía el modelo almacenado incorrectamente.

Se volvió a seleccionar manualmente desde la lista de modelos.

El problema desapareció.

---

## Problema 4

### access to env vars denied

El HTTP Request utilizaba:

```
{{$env.NVIDIA_API_KEY}}
```

y

```
{{$env.NVIDIA_API_BASE}}
```

n8n bloqueaba acceso a variables.

Se solucionó agregando:

```
N8N_BLOCK_ENV_ACCESS_IN_NODE=false
```

al compose.

También se verificó:

```
NVIDIA_API_KEY
NVIDIA_API_BASE
```

dentro del contenedor.

Después de recrear Docker:

```
docker compose down
docker compose up -d --build --force-recreate
```

el problema desapareció.

---

## Problema 5

### PostgreSQL ocupando puerto

El sistema tenía PostgreSQL instalado localmente.

Docker no podía usar:

```
5432
```

Se detuvo el servicio:

```
sudo systemctl stop postgresql
```

Después Docker inició correctamente.

---

## Problema 6

### Fetch Jerga

Se detectó un error DNS.

Finalmente se descubrió que la conexión debía realizarse mediante:

```
localhost
```

y no mediante el nombre del contenedor.

El nodo volvió a funcionar.

---

## Problema 7

### Python runner

Regex Pre-filter estaba implementado en Python.

n8n Community no dispone del runner Python.

Aparecía:

```
Python runner unavailable
```

Se migró completamente el nodo a JavaScript.

Beneficios:

* no depende del runner Python
* mayor compatibilidad
* ejecución inmediata

---

## Problema 8

### Constraint de PostgreSQL

Store Result produce actualmente:

```
results_severity_check
```

El Regex genera:

```
severity = drugs
```

pero la tabla espera niveles de severidad, no categorías.

Debe alinearse con el esquema real de la base de datos.

Este es el único bloqueo funcional restante.

---

# Estado actual del benchmark

Actualmente funcionan correctamente:

* Attack Config
* Generate Batch Items
* Loop Batch
* Fetch Jerga
* Attacker Agent
* Extract Adversarial Prompt
* Target NVIDIA NIM
* Extract Target Response
* Regex Pre-filter
* Skip Judge

El flujo ya alcanza Store Result.

---

# Trabajo pendiente

## Resolver constraint de PostgreSQL

Verificar qué valores acepta:

```
severity
```

y modificar:

* Regex
* Judge

para producir esos valores.

---

## Validar Judge

Comprobar que:

Normalize Judge Output

genere exactamente el mismo formato que espera PostgreSQL.

---

## Ejecutar benchmark completo

Una vez corregido Store Result:

* ejecutar 100 iteraciones
* validar inserciones
* revisar dashboards Grafana

---

# Estado general

El benchmark se encuentra aproximadamente al **95% de funcionamiento**.

Toda la infraestructura ya opera correctamente:

* Docker
* PostgreSQL
* NVIDIA NIM
* Attacker
* Target
* Regex
* Judge

El único bloqueo restante corresponde a la validación del esquema de la tabla `results`.

Una vez corregido ese detalle, el benchmark podrá ejecutarse completamente de principio a fin de manera automática.
