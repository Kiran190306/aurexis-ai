# Release Candidate Report

**Status: NOT COMPLETE — execution evidence is blocked by this workspace's missing Docker CLI.**

This report separates completed repository work from work that must be executed against a Docker engine or a Kubernetes cluster. No unexecuted check is reported as passing.

## Completed evidence

| Area | Evidence | Result |
| --- | --- | --- |
| Backend unit/integration tests | `python -m pytest tests/unit tests/integration -p no:cacheprovider` | **11 passed** (2026-07-11) |
| Python syntax | `python -m compileall -q backend/app backend/alembic` | **Passed** |
| Frontend production build | `npm.cmd run build` | **Passed** — 1,424 modules transformed (2026-07-11) |
| Dependency declaration hygiene | 82 unique direct pins in `backend/requirements.txt` (duplicate declarations removed) | **Passed** |
| Container audit design | `deploy/docker/backend/Dockerfile`, target `audit` installs `libpq-dev` (provides `pg_config`), then every pinned requirement | **Implemented** |
| Migration gate | Compose service `migrations` executes `alembic upgrade head`; Alembic converts the runtime `asyncpg` URL to a synchronous `psycopg2` URL | **Implemented** |
| Observability | `/metrics`, request count/latency metrics, Grafana provisioning/dashboard, OTLP configuration, JSON logging, `X-Request-ID`, `X-Correlation-ID`, liveness/readiness endpoints | **Implemented and unit-tested for IDs** |
| Rehearsal automation | `scripts/audit-dependencies.ps1` and `scripts/validate-production-compose.ps1` | **Implemented** |
| Static deployment assets | Both PowerShell scripts parse; Compose Dockerfile paths and Grafana dashboard JSON resolve correctly | **Passed** |

## Dependency vulnerability report

The audit is intentionally container-only. Its audit image includes PostgreSQL build prerequisites (`build-essential`, `libpq-dev`) and installs **all dependencies from `backend/requirements.txt`** before running:

```powershell
./scripts/audit-dependencies.ps1
```

Expected artifacts are `reports/python-dependencies.txt` (resolved complete package set), `reports/pip-audit.json`, `reports/safety.json`, and `reports/audit-summary.txt`. A clean run ends with exit code `0`; any reported vulnerability or scanner failure ends non-zero and blocks promotion.

**Execution result in this workspace: not run.** `docker` is not installed or available on `PATH`, so no container can be built and no scanner output exists. Consequently, there are **no accepted vulnerability risks** and no package upgrades have been made without scanner evidence and compatibility validation. The pinned dependency set is old enough that release promotion must remain blocked until the generated JSON files are reviewed.

## Docker validation and functional results

The following is executable and checks backend/frontend startup, PostgreSQL/Redis initialization, migrations, AI-engine readiness, health, auth, conversation, tool, memory, Prometheus, and Grafana:

```powershell
Copy-Item deploy/docker/.env.example deploy/docker/.env
# Replace placeholder secrets in deploy/docker/.env.
./scripts/validate-production-compose.ps1
```

Expected final output:

```text
PASS: Alembic migration completed
PASS: backend liveness (200)
PASS: backend readiness (200)
PASS: backend metrics (200)
PASS: frontend health (200)
PASS: authentication
PASS: conversation API
PASS: tool calling API
PASS: memory service
PASS: Prometheus readiness
PASS: Grafana health
RC Compose validation completed successfully.
```

**Execution result in this workspace: not run.** Exact limitation: `docker --version` fails because the `docker` executable is absent. This blocks image builds, Compose service startup, PostgreSQL/Redis initialization, migration execution, container health probes, endpoint/API validation, and the mandated container-only dependency audit.

## Production deployment rehearsal

The full Kubernetes command sequence, client-side manifest validation, backup verification, rollout checks, rollback commands, and graceful shutdown behavior are in [`deploy/PRODUCTION_REHEARSAL.md`](../deploy/PRODUCTION_REHEARSAL.md).

**Execution result in this workspace: not run.** Exact limitation: no Docker engine or Kubernetes cluster/`kubectl` is available. It prevents applying manifests, creating production secrets, running the migration Job, checking rollout health, and exercising backup/rollback. The runbook provides the exact commands and expected successful rollout output.

## Security and performance summary

- Structured logs avoid serializing request bodies or authorization headers; request/correlation IDs are included as log fields and response headers.
- Prometheus labels use HTTP method, path, and status only, avoiding query-string and user-ID cardinality leaks.
- Readiness requires successful PostgreSQL `SELECT 1`, Redis `PING`, and AI-engine startup; liveness remains independent of dependencies for correct restart behavior.
- Performance/load measurements were **not performed** because the Docker runtime is unavailable. No latency, throughput, CPU, or memory figures are asserted.

## Known limitations and remaining risks

1. Container audit, integration rehearsal, and Kubernetes rehearsal have no runtime evidence in this workspace. They are release-blocking until the commands above succeed and the report artifacts are retained.
2. No external LLM provider key is required to initialize the AI engine, but generation with OpenAI/Anthropic cannot be validated without a non-production test key and provider authorization.
3. Kubernetes observability is provisioned for Compose. A cluster needs its organization-approved Prometheus/Grafana/OTel collector installation and the configured `OTEL_EXPORTER_OTLP_ENDPOINT` before trace export can be verified.
4. The current local virtual environment lacks `redis` and OpenTelemetry packages; imports are lazy for test collection. The production Docker image installs the pinned packages. This does not substitute for the container validation.

## Promotion checklist

- [x] Automated local tests and compile check pass.
- [x] Audit, Compose, migration, observability, K8s, backup, rollback, and shutdown automation/configuration are committed.
- [ ] `pip-audit` and `safety` container reports generated and findings remediated/explicitly accepted.
- [ ] Docker Compose rehearsal completed with recorded output.
- [ ] Kubernetes dry-run, migration Job, rollout, backup/restore, and rollback rehearsal completed in the target environment.
- [ ] Performance/load report completed against the production-like environment.

Release Candidate status cannot be declared complete until every unchecked item has recorded execution evidence.
