# Deployment Guide

This directory contains deployment configurations for the Jarvis AI platform.

## Docker Deployment

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+

### Quick Start

1. Copy the Compose environment file:
```bash
cp deploy/docker/.env.example deploy/docker/.env
```

2. Edit `.env` with your configuration:
```bash
# Replace all placeholder values, including ADMIN_PASSWORD and
# GRAFANA_ADMIN_PASSWORD. Provider keys are optional.
```

3. Start services:
```bash
docker compose --env-file deploy/docker/.env -f deploy/docker/docker-compose.yml up -d --wait
```

4. Check status:
```bash
docker compose --env-file deploy/docker/.env -f deploy/docker/docker-compose.yml ps
docker compose --env-file deploy/docker/.env -f deploy/docker/docker-compose.yml logs -f
```

Run the complete audit and validation rehearsal with [`PRODUCTION_REHEARSAL.md`](PRODUCTION_REHEARSAL.md). The audit uses a dedicated Docker target with `libpq-dev`/`pg_config`; it must not be replaced by a host-only scan.

### Building Images

```bash
# Build backend
docker build -f deploy/docker/backend/Dockerfile -t jarvis-ai/backend:latest backend/

# Build frontend
docker build -f deploy/docker/frontend/Dockerfile -t jarvis-ai/frontend:latest frontend/
```

## Kubernetes Deployment

### Prerequisites
- kubectl 1.25+
- Kubernetes cluster (minikube, kind, or cloud provider)
- cert-manager (for TLS certificates)

### Setup

1. Create namespace:
```bash
kubectl create namespace jarvis
```

2. Configure secrets:
```bash
kubectl create secret generic jarvis-secrets \
  --from-literal=postgres-user=jarvis \
  --from-literal=postgres-password=your_password \
  --from-literal=database-url=postgresql+asyncpg://jarvis:your_password@jarvis-postgres:5432/jarvis \
  --from-literal=redis-url=redis://jarvis-redis:6379/0 \
  --from-literal=secret-key=your_secret_key \
  --from-literal=openai-api-key=your_openai_key \
  --from-literal=anthropic-api-key=your_anthropic_key \
  -n jarvis
```

3. Deploy PostgreSQL:
```bash
kubectl apply -f deploy/kubernetes/postgres-deployment.yaml -n jarvis
```

4. Deploy Redis:
```bash
kubectl apply -f deploy/kubernetes/redis-deployment.yaml -n jarvis
```

5. Deploy backend:
```bash
kubectl apply -f deploy/kubernetes/backend-deployment.yaml -n jarvis
```

6. Deploy frontend:
```bash
kubectl apply -f deploy/kubernetes/frontend-deployment.yaml -n jarvis
```

### Monitoring

```bash
# Check pod status
kubectl get pods -n jarvis

# View logs
kubectl logs -f deployment/jarvis-backend -n jarvis
kubectl logs -f deployment/jarvis-frontend -n jarvis

# Check services
kubectl get svc -n jarvis
```

### Scaling

```bash
# Scale backend
kubectl scale deployment jarvis-backend --replicas=5 -n jarvis

# Scale frontend
kubectl scale deployment jarvis-frontend --replicas=3 -n jarvis
```

## Production Checklist

- [ ] Change all default passwords and secrets
- [ ] Configure SSL/TLS certificates
- [ ] Set up monitoring and alerting (Prometheus, Grafana)
- [ ] Configure log aggregation (ELK stack, Loki)
- [ ] Enable backup strategy for PostgreSQL
- [ ] Configure CDN for static assets
- [ ] Set up rate limiting
- [ ] Configure WAF (Web Application Firewall)
- [ ] Enable audit logging
- [ ] Set up disaster recovery plan

## Security Considerations

- Use strong, unique passwords for all services
- Rotate secrets regularly
- Enable network policies in Kubernetes
- Use private container registry
- Scan images for vulnerabilities
- Enable RBAC in Kubernetes
- Use encrypted secrets (Sealed Secrets, Vault)

## Troubleshooting

### Backend not starting
```bash
# Check logs
kubectl logs deployment/jarvis-backend -n jarvis

# Check database connection
kubectl exec -it deployment/jarvis-backend -n jarvis -- pg_isready -h jarvis-postgres
```

### Frontend not loading
```bash
# Check nginx logs
kubectl logs deployment/jarvis-frontend -n jarvis

# Check ingress
kubectl describe ingress jarvis-ingress -n jarvis
```

### Database connection issues
```bash
# Check PostgreSQL pod
kubectl get pods -n jarvis -l app=jarvis-postgres

# Check PostgreSQL logs
kubectl logs -l app=jarvis-postgres -n jarvis
```

## Backup and Restore

### PostgreSQL Backup
```bash
kubectl exec -it deployment/jarvis-postgres -n jarvis -- pg_dump -U jarvis jarvis > backup.sql
```

### PostgreSQL Restore
```bash
cat backup.sql | kubectl exec -i deployment/jarvis-postgres -n jarvis -- psql -U jarvis jarvis
```

## Support

For deployment issues, refer to the main README or create an issue in the repository.
