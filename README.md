# Yucatan Slang Jailbreak Benchmark

An academic research benchmark designed to evaluate the robustness of Large Language Models against regional slang and colloquialisms. This project uses a multi-agent architecture to autonomously test LLM safety filters, utilizing Yucatecan slang to measure the limits of AI guardrails.

## 🏆 Achievements & Current State

- **OpenRouter Integration:** We successfully migrated the execution pipeline from NVIDIA NIM to OpenRouter! This allows unlimited API queries and enables us to test against a vast spectrum of models (from weak to frontier models).
- **First Jailbreaks Logged!** The Grafana dashboard is looking great and currently reflecting a **9.09% overall jailbreak success rate** against target models (including Gemini 2.5 Flash).
- **Multi-Agent Pipeline Active:** Complete end-to-end execution of the Attacker, Target, and Judge agents working asynchronously.
- **Live Visualizations:** Dashboard is live, dynamically displaying attack metrics, success rates by technique, and judge confidence with functional data pipelines flowing from the evaluation scripts straight to the visualizer!

## 🤖 Supported Target Models

We initially agreed on evaluating a range of models, including medium/weak models to guarantee baseline success, alongside harder frontier models. The active supported list via OpenRouter is:

### Primary Baseline Targets
- `openrouter/meta-llama/llama-3.1-8b-instruct`
- `openrouter/mistralai/mistral-7b-instruct-v0.3`
- `openrouter/qwen/qwen2-7b-instruct`
- `openrouter/google/gemma-2-9b-it`

### Frontier Targets (Harder Models)
- `openrouter/anthropic/claude-3.5-sonnet`
- `openrouter/openai/gpt-4o`
- `openrouter/google/gemini-2.5-flash`

## 🧠 Architecture

1. **Attacker Agent (Hermes 3 / Llama 3.1 405B)**: Crafts adversarial prompts dynamically using slang terms from the DB, utilizing seven distinct attack techniques (translation transfer, semantic obfuscation, roleplay wrap, crescendo, codeswitching, manyshot slang, pair refine).
2. **Target Agent (Swappable)**: The model being tested for safety filter robustness.
3. **Judge Agent (Llama 3.1 70B)**: Evaluates the target model's response via deterministic LLM call, returning a structured verdict (`jailbreak_success`, `confidence`, `severity`, `reasoning`).
4. **Storage Layer**: PostgreSQL database storing every attack attempt, response, and verdict.
5. **Visualization**: Grafana Dashboards for live telemetry.

## 🛠️ Setup & Execution

**1. Configure environment**
```bash
cp .env.example .env
# Open .env and set OPENROUTER_API_KEY to your OpenRouter API key
```

**2. Start the telemetry services (Postgres, Grafana, N8N)**
```bash
docker compose up -d --build
```

**3. Access the services**
```
n8n (workflow editor)  →  http://localhost:5678
Grafana (dashboards)   →  http://localhost:3000   (user: admin / pass: admin)
PostgreSQL             →  localhost:5432           (user: admin / db: slang_bench)
```

## Running the Python attacker (CLI)

`attacker/main.py` runs the full benchmark pipeline (`Fetch Jerga → Attacker → Target → Regex pre-filter → Judge → Storage`) from the command line.

**1. Install dependencies**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r attacker/requirements.txt
```

**2. Run a benchmark**
```bash
source .venv/bin/activate && export $(grep -v '^#' .env | xargs)

# 10 iterations against Gemini
python3 attacker/main.py run --limit 10 --target openrouter/google/gemini-2.5-flash

# Fixed technique against Llama
python3 attacker/main.py run \
  --target openrouter/meta-llama/llama-3.1-8b-instruct \
  --technique roleplay_wrap \
  --limit 100
```
