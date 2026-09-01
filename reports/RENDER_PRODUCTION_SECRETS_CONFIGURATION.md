# RENDER PRODUCTION SECRETS CONFIGURATION

**Date**: 2026-09-01
**Project**: Jarvis AI Enterprise Agent Platform
**EPIC**: JARVIS AI — FINAL RENDER PRODUCTION DEPLOYMENT
**Phase**: Phase 7 - Production Secrets Configuration

---

## Executive Summary

Production secrets configuration documented. All secrets must be configured in Render environment, never in code. Critical secrets identified: SECRET_KEY, ADMIN_PASSWORD, REDIS_PASSWORD, LLM API keys. Render provides secure environment variable management. No secrets should be committed to git or included in render.yaml.

**Status**: ✅ SECRETS CONFIGURATION DOCUMENTED

---

## Secrets Policy

### Golden Rule

**NEVER commit secrets to code or configuration files.**

All secrets must be configured in Render environment variables.

### Forbidden Locations

❌ **NEVER put secrets in**:
- render.yaml
- Dockerfile
- Source code
- .env files committed to git
- README.md
- Documentation files
- Git repository

### Allowed Locations

✅ **ONLY configure secrets in**:
- Render environment variables (dashboard)
- Render secrets management
- Local .env file (gitignored)

---

## Required Secrets

### Critical Secrets (Must Configure)

| Secret | Purpose | Render Service | Format | Notes |
|--------|---------|----------------|--------|-------|
| SECRET_KEY | JWT signing | All Services | Random string (32+ chars) | Generate with secrets.token_urlsafe(32) |
| ADMIN_PASSWORD | Admin account | All Services | Strong password (12+ chars) | Must be set in production |
| REDIS_PASSWORD | Redis auth | All Services | Strong password (16+ chars) | Provided by Render Redis service |
| DATABASE_URL | PostgreSQL | All Services | postgresql+asyncpg://... | Provided by Render PostgreSQL service |
| REDIS_URL | Redis connection | All Services | redis://:password@host:port/0 | Provided by Render Redis service |
| CELERY_BROKER_URL | Celery broker | Worker, Beat | redis://:password@host:port/1 | Construct from REDIS_URL |
| CELERY_RESULT_BACKEND | Celery results | Worker, Beat | redis://:password@host:port/2 | Construct from REDIS_URL |

### Optional LLM Secrets (Configure if Using LLM)

| Secret | Purpose | Render Service | Format | Notes |
|--------|---------|----------------|--------|-------|
| OPENAI_API_KEY | OpenAI LLM | All Services | sk-... | Get from OpenAI dashboard |
| ANTHROPIC_API_KEY | Anthropic LLM | All Services | sk-ant-... | Get from Anthropic dashboard |
| GOOGLE_API_KEY | Google LLM | All Services | AIza... | Get from Google Cloud |

---

## Render Secret Configuration

### Step 1: Access Render Dashboard

1. Log in to Render dashboard
2. Navigate to your service
3. Go to "Environment" tab

### Step 2: Add Environment Variables

For each secret:

1. Click "Add Environment Variable"
2. Enter variable name (e.g., SECRET_KEY)
3. Enter value (paste from secure location)
4. Mark as "Sensitive" (if available)
5. Save

### Step 3: Link Render Services

For DATABASE_URL and REDIS_URL:

1. Use "From Database" or "From Redis" option
2. Select the appropriate service
3. Render will automatically provide the connection string

---

## Secret Generation

### Generate SECRET_KEY

**Python**:
```python
import secrets
print(secrets.token_urlsafe(32))
```

**PowerShell**:
```powershell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
```

**Requirements**:
- Minimum 32 characters
- Random and unpredictable
- Store securely

### Generate ADMIN_PASSWORD

**Python**:
```python
import secrets
import string
alphabet = string.ascii_letters + string.digits + string.punctuation
password = ''.join(secrets.choice(alphabet) for _ in range(16))
print(password)
```

**Requirements**:
- Minimum 12 characters
- Mix of letters, numbers, symbols
- Store securely

### REDIS_PASSWORD

**Provided by Render**: Automatically generated when Redis service is created

**Access**: View in Render dashboard under Redis service

---

## Service-Specific Secret Configuration

### Frontend Web Service

**Required Secrets**:
- VITE_API_URL: Backend public URL (not secret, but required)

**Configuration**:
```yaml
envVars:
  - key: VITE_API_URL
    sync: false
    value: https://your-backend.onrender.com
```

### Backend Web Service

**Required Secrets**:
- APP_ENV: production
- SECRET_KEY: (generate)
- ADMIN_PASSWORD: (generate)
- DATABASE_URL: (from Render PostgreSQL)
- REDIS_URL: (from Render Redis, add /0)
- REDIS_PASSWORD: (from Render Redis)
- CELERY_BROKER_URL: (construct from REDIS_URL with /1)
- CELERY_RESULT_BACKEND: (construct from REDIS_URL with /2)
- CORS_ORIGINS: Frontend URL

**Optional Secrets**:
- OPENAI_API_KEY: (if using OpenAI)
- ANTHROPIC_API_KEY: (if using Anthropic)
- GOOGLE_API_KEY: (if using Google)

### Celery Worker Service

**Required Secrets**:
- Same as Backend Web Service
- (All backend secrets required for worker)

### Celery Beat Service

**Required Secrets**:
- Same as Backend Web Service
- (All backend secrets required for beat)

### Migration Job

**Required Secrets**:
- DATABASE_URL: (from Render PostgreSQL)

---

## URL Construction

### DATABASE_URL Construction

**Render provides**: `postgres://user:pass@host:port/db`

**Application needs**: `postgresql+asyncpg://user:pass@host:port/db`

**Conversion**:
```python
# Option 1: Set custom DATABASE_URL in Render
DATABASE_URL = postgresql+asyncpg://user:pass@host:port/db

# Option 2: Convert in application code (not recommended)
DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://")
```

**Recommendation**: Set custom DATABASE_URL in Render with asyncpg format

### REDIS_URL Construction

**Render provides**: `rediss://default:password@host:port`

**Application needs**: `redis://:password@host:port/db`

**Conversion**:
```python
# Base URL (database 0)
REDIS_URL = rediss://:password@host:port/0

# Celery broker (database 1)
CELERY_BROKER_URL = rediss://:password@host:port/1

# Celery result backend (database 2)
CELERY_RESULT_BACKEND = rediss://:password@host:port/2
```

**Notes**:
- Remove `default:` from URL
- Add database number
- Keep password
- Keep host and port

---

## Secret Rotation

### Rotation Policy

**Recommended Rotation**:
- SECRET_KEY: Rotate annually or if compromised
- ADMIN_PASSWORD: Rotate quarterly or if compromised
- REDIS_PASSWORD: Rotate when Redis service recreated
- LLM API Keys: Rotate if compromised or expired

### Rotation Procedure

1. Generate new secret
2. Update Render environment variable
3. Redeploy affected services
4. Verify functionality
5. Invalidate old secret (if applicable)

---

## Secret Storage Best Practices

### Local Development

**Use .env file** (gitignored):
```bash
SECRET_KEY=dev-secret-key
ADMIN_PASSWORD=dev-password
```

**Never commit .env to git**

### Production

**Use Render environment variables**:
- Configure in Render dashboard
- Mark as sensitive
- Never commit to code

### Secret Sharing

**Never share secrets via**:
- Email
- Chat
- Unencrypted files
- Screenshots

**Share secrets via**:
- Render dashboard (team access)
- Password manager (1Password, LastPass)
- Encrypted file (if necessary)

---

## Secret Verification

### Verification Checklist

Before deployment, verify:

- [ ] SECRET_KEY is set and is 32+ characters
- [ ] ADMIN_PASSWORD is set and is 12+ characters
- [ ] REDIS_PASSWORD is set (from Render Redis)
- [ ] DATABASE_URL is set (from Render PostgreSQL)
- [ ] REDIS_URL is set (from Render Redis with /0)
- [ ] CELERY_BROKER_URL is set (with /1)
- [ ] CELERY_RESULT_BACKEND is set (with /2)
- [ ] CORS_ORIGINS is set to frontend URL
- [ ] VITE_API_URL is set to backend URL
- [ ] LLM API keys are set (if using LLM)
- [ ] No secrets in render.yaml
- [ ] No secrets in Dockerfile
- [ ] No secrets in source code
- [ ] No secrets in committed .env files

---

## Security Considerations

### Secret Exposure Risks

**Risks**:
- Secrets in git repository
- Secrets in logs
- Secrets in error messages
- Secrets in frontend code

**Mitigation**:
- Never commit secrets
- Configure logging to exclude secrets
- Use environment variables
- Never put secrets in frontend build

### Render Security Features

**Render provides**:
- Encrypted environment variables at rest
- Encrypted environment variables in transit
- Access control via Render dashboard
- Audit logs for environment variable changes

**Best practices**:
- Enable Render team access control
- Use Render's sensitive flag
- Monitor environment variable changes
- Rotate secrets regularly

---

## Troubleshooting

### Secret Not Working

**Symptoms**:
- Service fails to start
- Authentication errors
- Database connection errors
- Redis connection errors

**Possible Causes**:
1. Secret not set in Render
2. Secret name mismatch
3. Secret value incorrect
4. Secret format incorrect

**Solutions**:
1. Verify secret is set in Render dashboard
2. Verify secret name matches code
3. Verify secret value is correct
4. Verify secret format (URL format, etc.)

### Secret Rotation Issues

**Symptoms**:
- Services fail after rotation
- Authentication failures
- Connection failures

**Solutions**:
1. Redeploy all affected services
2. Verify new secret is propagated
3. Verify old secret is invalidated
4. Rollback if necessary

---

## Sign-Off

**Secrets Configuration Date**: 2026-09-01
**Secrets Configuration By**: Cascade AI Assistant
**EPIC**: JARVIS AI — FINAL RENDER PRODUCTION DEPLOYMENT
**Phase**: Phase 7 - Production Secrets Configuration
**Status**: ✅ SECRETS CONFIGURATION DOCUMENTED

**Overall Assessment**: Production secrets configuration documented. All secrets must be configured in Render environment, never in code. Critical secrets: SECRET_KEY, ADMIN_PASSWORD, REDIS_PASSWORD, DATABASE_URL, REDIS_URL, CELERY_BROKER_URL, CELERY_RESULT_BACKEND. Optional LLM secrets: OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY. Render provides secure environment variable management. URL construction required for DATABASE_URL and REDIS_URL.

**Next Phase**: Phase 8 - Frontend Production Configuration
