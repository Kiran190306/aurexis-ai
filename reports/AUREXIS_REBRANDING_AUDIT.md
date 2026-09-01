# AUREXIS REBRANDING AUDIT

**Date**: 2026-09-01
**Project**: Jarvis AI → Aurexis AI Rebranding
**EPIC**: AUREXIS — COMPLETE BRAND RENAMING / REBRANDING

---

## Executive Summary

This audit catalogs all occurrences of "Jarvis", "JARVIS", and "jarvis" in the repository to guide the rebranding effort from "Jarvis AI" to "Aurexis AI". Each occurrence is classified by category with recommended action and risk level.

**Total Occurrences Found**: 30+ across 11 files

---

## Audit Results

### 1. README.md

**File**: `README.md`

| Line | Reference | Category | Recommended Action | Risk Level |
|------|-----------|----------|-------------------|------------|
| 1 | `# Jarvis AI - Enterprise AI Agent Platform` | User-facing branding | CHANGE to "Aurexis AI" | LOW |
| 10 | `Jarvis AI is an enterprise-grade...` | Documentation | CHANGE to "Aurexis AI" | LOW |
| 43 | `Jarvis AI follows a modular...` | Documentation | CHANGE to "Aurexis AI" | LOW |
| 70 | `git clone https://github.com/your-org/jarvis-ai.git` | Documentation | CHANGE to `aurexis-ai` | LOW |
| 71 | `cd jarvis-ai` | Documentation | CHANGE to `aurexis-ai` | LOW |
| 126 | `jarvis-ai/` | Documentation | CHANGE to `aurexis-ai/` | LOW |
| 309 | `https://github.com/your-org/jarvis-ai/issues` | Documentation | CHANGE to `aurexis-ai` | LOW |
| 310 | `https://github.com/your-org/jarvis-ai/discussions` | Documentation | CHANGE to `aurexis-ai` | LOW |
| 349 | `contact@jarvis-ai.com` | Documentation | CHANGE to `contact@aurexis-ai.com` | LOW |
| 350 | `@jarvis_ai` | Documentation | CHANGE to `@aurexis_ai` | LOW |
| 351 | `https://discord.gg/jarvis-ai` | Documentation | CHANGE to `aurexis-ai` | LOW |

---

### 2. backend/app/core/config.py

**File**: `backend/app/core/config.py`

| Line | Reference | Category | Recommended Action | Risk Level |
|------|-----------|----------|-------------------|------------|
| 10 | `APP_NAME: str = "Jarvis AI"` | Configuration | CHANGE to "Aurexis AI" | LOW |
| 25 | `postgresql+asyncpg://jarvis:changeme@localhost:5432/jarvis` | Database identifier | KEEP - internal DB user/db name | MEDIUM |
| 100 | `CHROMA_COLLECTION_NAME: str = "jarvis_memory"` | Database identifier | KEEP - ChromaDB collection name | MEDIUM |
| 144 | `OTEL_SERVICE_NAME: str = "jarvis-backend"` | Monitoring | CHANGE to "aurexis-backend" | LOW |
| 152 | `SMTP_FROM: str = "noreply@jarvis-ai.com"` | Configuration | CHANGE to "noreply@aurexis-ai.com" | LOW |
| 241 | `ADMIN_EMAIL: str = "admin@jarvis-ai.com"` | Configuration | CHANGE to "admin@aurexis-ai.com" | LOW |
| 190 | `WAKE_WORD_PHRASE: str = "hey jarvis"` | Configuration | CHANGE to "hey aurexis" | LOW |

---

### 3. frontend/package.json

**File**: `frontend/package.json`

| Line | Reference | Category | Recommended Action | Risk Level |
|------|-----------|----------|-------------------|------------|
| 2 | `"name": "jarvis-ai-frontend"` | Package metadata | CHANGE to "aurexis-ai-frontend" | LOW |

---

### 4. render.yaml

**File**: `render.yaml`

| Line | Reference | Category | Recommended Action | Risk Level |
|------|-----------|----------|-------------------|------------|
| 4 | `name: jarvis-frontend` | Service naming | CHANGE to "aurexis-frontend" | LOW |
| 17 | `name: jarvis-backend` | Service naming | CHANGE to "aurexis-backend" | LOW |
| 34 | `name: jarvis-postgres` | Database identifier | KEEP - Render DB name | HIGH (requires DB recreation) |
| 39 | `name: jarvis-redis` | Service naming | CHANGE to "aurexis-redis" | MEDIUM |
| 67 | `name: jarvis-celery-worker` | Service naming | CHANGE to "aurexis-celery-worker" | LOW |
| 108 | `name: jarvis-celery-beat` | Service naming | CHANGE to "aurexis-celery-beat" | LOW |
| 149 | `name: jarvis-migrations` | Service naming | CHANGE to "aurexis-migrations" | LOW |
| 166 | `databaseName: jarvis` | Database identifier | KEEP - Render DB name | HIGH (requires DB recreation) |
| 167 | `user: jarvis` | Database identifier | KEEP - Render DB user | HIGH (requires DB recreation) |

---

### 5. frontend/src/pages/DashboardPage.tsx

**File**: `frontend/src/pages/DashboardPage.tsx`

| Line | Reference | Category | Recommended Action | Risk Level |
|------|-----------|----------|-------------------|------------|
| 25 | `Here's what's happening with your Jarvis AI` | User-facing branding | CHANGE to "Aurexis AI" | LOW |

---

### 6. frontend/src/pages/auth/LoginPage.tsx

**File**: `frontend/src/pages/auth/LoginPage.tsx`

| Line | Reference | Category | Recommended Action | Risk Level |
|------|-----------|----------|-------------------|------------|
| 34 | `Sign in to your Jarvis AI account` | User-facing branding | CHANGE to "Aurexis AI" | LOW |

---

### 7. frontend/src/components/layout/Layout.tsx

**File**: `frontend/src/components/layout/Layout.tsx`

| Line | Reference | Category | Recommended Action | Risk Level |
|------|-----------|----------|-------------------|------------|
| 56 | `<h1 className="text-xl font-bold text-foreground">Jarvis AI</h1>` | User-facing branding | CHANGE to "Aurexis AI" | LOW |

---

### 8. frontend/index.html

**File**: `frontend/index.html`

| Line | Reference | Category | Recommended Action | Risk Level |
|------|-----------|----------|-------------------|------------|
| 7 | `<title>Jarvis AI</title>` | User-facing branding | CHANGE to "Aurexis AI" | LOW |

---

### 9. backend/app/main.py

**File**: `backend/app/main.py`

| Line | Reference | Category | Recommended Action | Risk Level |
|------|-----------|----------|-------------------|------------|
| 47 | `logger.info("Starting Jarvis AI Backend...")` | Logging | CHANGE to "Aurexis AI" | LOW |
| 60 | `logger.info("Jarvis AI Backend started successfully")` | Logging | CHANGE to "Aurexis AI" | LOW |
| 63 | `logger.info("Shutting down Jarvis AI Backend...")` | Logging | CHANGE to "Aurexis AI" | LOW |
| 67 | `logger.info("Jarvis AI Backend stopped")` | Logging | CHANGE to "Aurexis AI" | LOW |
| 187 | `"message": "Welcome to Jarvis AI API"` | API identifier | CHANGE to "Aurexis AI" | LOW |

---

### 10. backend/app/worker.py

**File**: `backend/app/worker.py`

| Line | Reference | Category | Recommended Action | Risk Level |
|------|-----------|----------|-------------------|------------|
| 22 | `'jarvis_worker'` | Celery app name | CHANGE to "aurexis_worker" | MEDIUM |

---

### 11. deploy/docker/docker-compose.yml

**File**: `deploy/docker/docker-compose.yml`

| Line | Reference | Category | Recommended Action | Risk Level |
|------|-----------|----------|-------------------|------------|
| 1 | `name: jarvis-production-validation` | Docker compose project | CHANGE to "aurexis-production-validation" | LOW |
| 20 | `networks: [jarvis-network]` | Docker network | CHANGE to "aurexis-network" | LOW |
| 55 | `OTEL_SERVICE_NAME: jarvis-backend` | Monitoring | CHANGE to "aurexis-backend" | LOW |
| 215 | `jarvis-network:` | Docker network | CHANGE to "aurexis-network" | LOW |

---

## Summary by Category

### User-Facing Branding (CHANGE - LOW RISK)
- README.md title and descriptions
- Frontend page titles and text
- Frontend sidebar logo
- Frontend HTML title
- API welcome message

### Configuration (CHANGE - LOW RISK)
- APP_NAME
- Package names
- Service names
- Monitoring service names
- Email addresses
- Wake word phrase

### Database Identifiers (KEEP - MEDIUM/HIGH RISK)
- DATABASE_URL user/db (jarvis:changeme@localhost:5432/jarvis)
- CHROMA_COLLECTION_NAME (jarvis_memory)
- Render database name (jarvis)
- Render database user (jarvis)

**Rationale**: Changing database identifiers requires database migration/recreation which is risky for production compatibility. These are internal identifiers not visible to end users.

### Docker/Deployment (CHANGE - LOW/MEDIUM RISK)
- Docker compose project name
- Docker network names
- Render service names
- Celery app name

### Documentation (CHANGE - LOW RISK)
- GitHub repository references
- Contact information
- Social media handles

---

## Risk Assessment

### LOW RISK (Safe to Change)
- User-facing text
- Documentation
- Configuration values
- Service names (non-database)
- Package names
- Monitoring identifiers

### MEDIUM RISK (Review Before Change)
- Celery app name (affects task queue naming)
- Render Redis service name (affects service discovery)
- Docker network names (affects container networking)

### HIGH RISK (DO NOT CHANGE)
- Render database name (jarvis)
- Render database user (jarvis)
- Database URL identifiers (jarvis user/db)
- ChromaDB collection name (jarvis_memory)

**Rationale**: Database identifiers are critical for production compatibility. Changing them would require database migration/recreation which is outside the scope of a branding-only change.

---

## Recommended Action Plan

### Phase 2: User-Facing Branding (CHANGE)
1. README.md - Update all user-facing references
2. frontend/src/pages/DashboardPage.tsx - Update text
3. frontend/src/pages/auth/LoginPage.tsx - Update text
4. frontend/src/components/layout/Layout.tsx - Update logo
5. frontend/index.html - Update title
6. backend/app/main.py - Update log messages and API message

### Phase 3: Frontend (CHANGE)
1. frontend/package.json - Update package name

### Phase 4: Backend (CHANGE - Safe Only)
1. backend/app/core/config.py - Update APP_NAME, OTEL_SERVICE_NAME, SMTP_FROM, ADMIN_EMAIL, WAKE_WORD_PHRASE
2. backend/app/worker.py - Update Celery app name

### Phase 5: Docker/Deployment (CHANGE - Safe Only)
1. deploy/docker/docker-compose.yml - Update project name, network names, OTEL_SERVICE_NAME
2. render.yaml - Update service names (EXCEPT database name/user)

### Phase 6: Environment Variables (KEEP)
- No JARVIS_* environment variables found
- Keep all existing environment variables unchanged

### Phase 7: Database (KEEP)
- Keep DATABASE_URL user/db (jarvis)
- Keep CHROMA_COLLECTION_NAME (jarvis_memory)
- Keep Render database name (jarvis)
- Keep Render database user (jarvis)

---

## Total Count

- **CHANGE (Low Risk)**: 24 occurrences
- **CHANGE (Medium Risk)**: 3 occurrences
- **KEEP (Medium Risk)**: 2 occurrences
- **KEEP (High Risk)**: 4 occurrences

**Total**: 33 occurrences

---

## Sign-Off

**Audit Date**: 2026-09-01
**Audited By**: Cascade AI Assistant
**EPIC**: AUREXIS — COMPLETE BRAND RENAMING / REBRANDING
**Phase**: Phase 1 - Full Repository Audit
**Status**: ✅ COMPLETE
