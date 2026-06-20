# Changelog

All notable changes to the Yucatan Slang Jailbreak Benchmark are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Docker infrastructure: `compose.yml` orchestrating three services — PostgreSQL,
  n8n, and Grafana — on a shared `slang_net` bridge network.
- Per-service Dockerfiles under `docker/`:
  - `docker/postgres/Dockerfile` — `postgres:16` with a first-boot init hook
    (`init/` mounted into `/docker-entrypoint-initdb.d/`).
  - `docker/n8n/Dockerfile` — `n8nio/n8n`, using its first-party PostgreSQL node.
  - `docker/grafana/Dockerfile` — Grafana using its built-in, signed PostgreSQL
    datasource (no community plugin required).
- Grafana provisioning: PostgreSQL datasource and dashboard provider wired via
  `docker/grafana/provisioning/`.
- `.env.example` template documenting all configuration variables.

### Changed
- Storage backend is PostgreSQL: the `postgres` service replaces MongoDB, and the
  n8n / Grafana services connect over `POSTGRES_*` env vars instead of `MONGO_URL`.
- Restricted all LLM calls (attacker, targets, judge) to NVIDIA NIM only.
  Removed Gemini, Anthropic, Groq, and local Ollama configuration.
- Trimmed the `AGENTS.md` Supported Targets table to the four NVIDIA NIM models
  and updated the "Adding a New Target LLM" guide accordingly.
- Grafana dashboard mount now points at the `./grafana` directory instead of a
  single (possibly missing) JSON file.

[Unreleased]: https://example.com/compare/HEAD
