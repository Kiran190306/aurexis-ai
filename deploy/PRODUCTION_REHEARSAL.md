# Production deployment rehearsal

This runbook is executable against the Compose environment and provides the Kubernetes command sequence for an equivalent rehearsal. It does not accept placeholder secrets.

## Docker Compose

From the repository root:

```powershell
Copy-Item deploy/docker/.env.example deploy/docker/.env
# Replace every `replace-with-...` value in deploy/docker/.env.
./scripts/audit-dependencies.ps1
./scripts/validate-production-compose.ps1
```

Expected final output is `RC Compose validation completed successfully.` The first command writes `reports/pip-audit.json`, `reports/safety.json`, `reports/python-dependencies.txt`, and `reports/audit-summary.txt`. Either scanner returning findings intentionally returns a non-zero exit code and blocks release promotion.

The validation starts PostgreSQL, Redis, an Alembic one-shot migration service, API, frontend, Prometheus, and Grafana. It verifies liveness, readiness, `/metrics`, frontend health, a registration/login token flow, and create operations for conversations, tools, and memory.

## Kubernetes deployment sequence

Create secrets only through a secret manager integration or the explicit command below; do not apply `secrets.yaml` with literal placeholders.

```bash
kubectl create namespace jarvis
kubectl -n jarvis create secret generic jarvis-secrets \
  --from-literal=DATABASE_URL='postgresql+asyncpg://jarvis:REDACTED@jarvis-postgres:5432/jarvis' \
  --from-literal=REDIS_URL='redis://jarvis-redis:6379/0' \
  --from-literal=SECRET_KEY='REDACTED' \
  --from-literal=ADMIN_PASSWORD='REDACTED'
kubectl -n jarvis apply --dry-run=client -f deploy/kubernetes/
kubectl -n jarvis apply -f deploy/kubernetes/runtime-config.yaml
kubectl -n jarvis apply -f deploy/kubernetes/postgres-deployment.yaml -f deploy/kubernetes/redis-deployment.yaml
kubectl -n jarvis rollout status statefulset/jarvis-postgres --timeout=180s
kubectl -n jarvis rollout status deployment/jarvis-redis --timeout=180s
kubectl -n jarvis apply -f deploy/kubernetes/migration-job.yaml
kubectl -n jarvis wait --for=condition=complete job/jarvis-migrations --timeout=180s
kubectl -n jarvis apply -f deploy/kubernetes/backend-deployment.yaml -f deploy/kubernetes/frontend-deployment.yaml
kubectl -n jarvis rollout status deployment/jarvis-backend --timeout=180s
kubectl -n jarvis rollout status deployment/jarvis-frontend --timeout=180s
```

Expected output ends with `deployment "jarvis-backend" successfully rolled out` and `deployment "jarvis-frontend" successfully rolled out`.

## Rollback, backup, shutdown

Before every migration, capture a verified backup:

```bash
kubectl -n jarvis exec statefulset/jarvis-postgres -- pg_dump -U "$POSTGRES_USER" -Fc "$POSTGRES_DB" > "jarvis-$(date +%F-%H%M).dump"
pg_restore --list "jarvis-$(date +%F-%H%M).dump"
```

If a rollout fails, stop promotion, restore the prior API/frontend revisions, then restore the database only if the migration is not backward compatible:

```bash
kubectl -n jarvis rollout undo deployment/jarvis-backend
kubectl -n jarvis rollout undo deployment/jarvis-frontend
kubectl -n jarvis rollout status deployment/jarvis-backend --timeout=180s
```

The API receives SIGTERM, stops accepting work through readiness failure, flushes OpenTelemetry spans, disposes database connections, and exits. The five-second `preStop` delay lets endpoints drain before the process is terminated.
